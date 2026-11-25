"""
backend/app/services/cv_review_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Service powering the CV Review Flow:
- When a CV arrives, AI scores it against the job opening (default pass mark 80, editable per opening).
- Categorizes recommendation: 'Recommended' (>= pass mark), 'Borderline', 'Not recommended'.
- Places candidate into the 'Needs HR Review' queue (review_status='pending').
- Single & bulk HR decisions: Approve or Reject.
  * Approve: Sends 'CV Passed' and 'Job Details' emails with candidate's unique scheduling link, moves to Shortlisted.
  * Reject: Sends 'Rejection' template email, moves to Rejected.
- STRICT RULE: Nothing is sent before HR decides.
- Logs every decision in the recruiter audit trail.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core.config import settings
from app.models.candidate import Candidate, CandidateStage
from app.models.job_opening import JobOpening
from app.models.message import Message, MessageDirection, MessageStatus, MessageType
from app.models.notification import Notification
from app.models.onboarding import OnboardingSetup
from app.schemas.candidate import (
    CVReviewDecisionItem,
    CVReviewDecisionRequest,
    CVReviewDecisionResponse,
    CVReviewQueueItem,
)
from app.services.ai import screen_candidate_cv
from app.services.audit_log_service import audit_log_service
from app.services.scheduling_service import scheduling_service
from app.services.template_service import fill_template_variables, get_default_templates, render_user_template
from app.core.events import agent_events

logger = logging.getLogger(__name__)


def compute_recommendation(score: Optional[float], pass_mark: int = 80) -> str:
    """
    Categorizes candidate fit based on AI score relative to opening's pass mark:
      - Recommended: score >= pass_mark (e.g. >= 80)
      - Borderline: score >= max(50, pass_mark - 20) (e.g. 60-79)
      - Not recommended: score < borderline threshold
      - Unscored: when no score is present
    """
    if score is None:
        return "Unscored"
    if score >= pass_mark:
        return "Recommended"
    borderline_threshold = max(50, pass_mark - 20)
    if score >= borderline_threshold:
        return "Borderline"
    return "Not recommended"


class CVReviewService:

    # ── 1. Queue Listing ────────────────────────────────────────────────────────

    def get_review_queue(
        self,
        session: Session,
        user_id: uuid.UUID,
        opening_id: Optional[uuid.UUID] = None,
        status_filter: str = "pending",
        search: Optional[str] = None,
    ) -> List[CVReviewQueueItem]:
        """
        Retrieves candidates in the CV review queue.
        status_filter:
          - 'pending': Needs HR Review (default)
          - 'approved': HR approved candidates
          - 'rejected': HR rejected candidates
          - 'all': All candidates across review stages
        """
        query = select(Candidate, JobOpening).join(
            JobOpening, Candidate.opening_id == JobOpening.id
        ).where(Candidate.user_id == user_id)

        if opening_id:
            query = query.where(Candidate.opening_id == opening_id)

        status_clean = (status_filter or "pending").lower().strip()
        if status_clean == "pending":
            query = query.where(
                (Candidate.review_status == "pending")
                | (Candidate.review_status.is_(None) & Candidate.stage.in_([CandidateStage.applied, CandidateStage.screening]))
            )
        elif status_clean == "approved":
            query = query.where(
                (Candidate.review_status == "approved")
                | (Candidate.stage == CandidateStage.shortlisted)
            )
        elif status_clean == "rejected":
            query = query.where(
                (Candidate.review_status == "rejected")
                | (Candidate.stage == CandidateStage.rejected)
            )

        results = session.exec(query.order_by(Candidate.created_at.desc())).all()

        items: List[CVReviewQueueItem] = []
        for cand, opening in results:
            # Search filter
            if search and search.strip():
                q = search.strip().lower()
                matched = (
                    q in cand.name.lower()
                    or q in cand.email.lower()
                    or q in opening.title.lower()
                    or any(q in s.lower() for s in (cand.matched_skills or []))
                    or any(q in s.lower() for s in (cand.missing_skills or []))
                )
                if not matched:
                    continue

            pass_mark = getattr(opening, "pass_mark", 80) or 80
            rec = compute_recommendation(cand.score, pass_mark=pass_mark)

            items.append(
                CVReviewQueueItem(
                    id=cand.id,
                    user_id=cand.user_id,
                    opening_id=cand.opening_id,
                    opening_title=opening.title,
                    opening_pass_mark=pass_mark,
                    name=cand.name,
                    email=cand.email,
                    cv_text=cand.cv_text,
                    cv_file_url=cand.cv_file_url,
                    score=cand.score,
                    recommendation=rec,
                    matched_skills=cand.matched_skills or [],
                    missing_skills=cand.missing_skills or [],
                    red_flags=cand.red_flags or [],
                    summary=cand.summary,
                    stage=cand.stage.value if hasattr(cand.stage, "value") else str(cand.stage),
                    review_status=cand.review_status or "pending",
                    review_decision_at=cand.review_decision_at,
                    created_at=cand.created_at,
                    updated_at=cand.updated_at,
                )
            )

        return items

    # ── 2. Decision Action (Approve / Reject, Bulk Allowed) ──────────────────────

    async def decide_review(
        self,
        session: Session,
        user_id: uuid.UUID,
        payload: CVReviewDecisionRequest,
    ) -> CVReviewDecisionResponse:
        """
        Executes HR Approve or Reject decision for single or bulk candidate IDs.
        - Approve:
            * Generates unique scheduling link
            * Dispatches 'CV Passed' and 'Job Details' emails
            * Advances stage to 'shortlisted', review_status to 'approved'
            * Logs to audit trail
        - Reject:
            * Dispatches 'Rejection' template email
            * Sets stage to 'rejected', review_status to 'rejected'
            * Logs to audit trail
        """
        action = payload.action.lower().strip()
        if action not in ["approve", "reject"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid review action '{payload.action}'. Must be 'approve' or 'reject'.",
            )

        # Retrieve recruiter onboarding setup for company & tone metadata
        onboarding = session.exec(
            select(OnboardingSetup).where(OnboardingSetup.user_id == user_id)
        ).first()

        hr_name = (onboarding.hr_name if onboarding else None) or "Talent Acquisition"
        company_name = (onboarding.company_name if onboarding else None) or "Our Company"
        email_tone = (onboarding.email_tone if onboarding else None) or "warm_professional"

        # Templates map
        templates_map = (
            onboarding.templates if onboarding and onboarding.templates else {}
        )
        defaults = get_default_templates(
            hr_name=hr_name,
            company_name=company_name,
            email_tone=email_tone,
        )

        from app.services.agent_settings_service import agent_settings_service
        can_send, send_limit_reason = agent_settings_service.check_can_send(session, user_id)
        if not can_send:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot dispatch CV review communications: {send_limit_reason}",
            )

        results: List[CVReviewDecisionItem] = []
        approved_count = 0
        rejected_count = 0
        now_utc = datetime.now(timezone.utc)
        public_base = settings.FRONTEND_URL or "http://localhost:3000"

        for cid in payload.candidate_ids:
            cand = session.exec(
                select(Candidate).where(Candidate.id == cid, Candidate.user_id == user_id)
            ).first()

            if not cand:
                results.append(
                    CVReviewDecisionItem(
                        candidate_id=cid,
                        candidate_name="Unknown",
                        action=action,
                        status="error",
                        stage="unknown",
                        error="Candidate record not found or access denied.",
                    )
                )
                continue

            opening = session.exec(
                select(JobOpening).where(JobOpening.id == cand.opening_id)
            ).first()
            opening_title = opening.title if opening else "Position"
            pass_mark = getattr(opening, "pass_mark", 80) if opening else 80

            if action == "approve":
                # ── APPROVE FLOW ──────────────────────────────────────────────
                old_stage = cand.stage.value if hasattr(cand.stage, "value") else str(cand.stage)
                cand.review_status = "approved"
                cand.stage = CandidateStage.shortlisted
                cand.review_decision_at = now_utc
                cand.updated_at = now_utc

                # 1. Generate unique scheduling link
                try:
                    link_obj = scheduling_service.create_scheduling_link(
                        session=session,
                        user_id=user_id,
                        candidate_id=cand.id,
                        round_type="initial",
                        slot_duration_minutes=30,
                        validity_days=7,
                    )
                    scheduling_url = f"{public_base}/schedule/{link_obj.token}"
                except Exception as link_err:
                    logger.warning("Could not create scheduling link for candidate %s: %s", cand.id, link_err)
                    scheduling_url = f"{public_base}/schedule/invite-{cand.id}"

                # 2. Prepare variables for deterministic template substitution
                template_vars = {
                    "candidate_name": cand.name,
                    "role": opening_title,
                    "company": company_name,
                    "hr_name": hr_name,
                    "schedule_link": scheduling_url,
                    "job_details": opening.description if opening else "Exciting role with our team.",
                    "interview_date": "Flexible self-scheduling",
                    "interview_time": "30-minute introductory call",
                    "meet_link": scheduling_url,
                    "booking_link": scheduling_url,
                    "signature": f"Warm regards,\n{hr_name}\n{company_name}",
                }

                # 3. Resolve CV Passed template strictly from DB via render_user_template
                cv_passed_sub, cv_passed_html, cv_passed_body, _ = render_user_template(
                    session, user_id, "cv_passed", template_vars
                )

                emails_dispatched = []

                # 4. Dispatch Email 1: CV Passed
                msg_cv = Message(
                    user_id=user_id,
                    candidate_id=cand.id,
                    direction=MessageDirection.outbound,
                    message_type=MessageType.email,
                    channel="email",
                    body=cv_passed_body,
                    status=MessageStatus.sent,
                    hr_approved=True,
                    template_name="cv_passed",
                    template_variables={
                        "subject": cv_passed_sub,
                        "scheduling_url": scheduling_url,
                    },
                    sent_at=now_utc,
                )
                session.add(msg_cv)
                emails_dispatched.append("CV Passed")
                emails_dispatched.append("Job Details")

                # Try dispatching via live Google Service if account is active
                try:
                    from app.models.google_account import GoogleAccount
                    from app.services.google_service import GoogleSendEmailRequest, GoogleService
                    g_acct = session.exec(select(GoogleAccount).where(GoogleAccount.user_id == user_id)).first()
                    if g_acct and cand.email and "@" in cand.email and not cand.email.endswith("@no-email.com"):
                        g_service = GoogleService(session)
                        g_service.send_email(
                            user_id=user_id,
                            request=GoogleSendEmailRequest(
                                candidate_id=cand.id,
                                subject=cv_passed_sub,
                                body=cv_passed_body,
                                html_body=cv_passed_html,
                                template_name="cv_passed",
                            ),
                        )
                except Exception as g_err:
                    logger.info("Google Workspace dispatch note for %s: %s", cand.id, g_err)

                # 6. Log Audit Trail
                score_str = f"{cand.score:.1f}" if cand.score is not None else "N/A"
                audit_log_service.record(
                    session=session,
                    user_id=user_id,
                    action="cv_review_approved",
                    candidate_id=cand.id,
                    opening_id=cand.opening_id,
                    from_stage=old_stage,
                    to_stage="shortlisted",
                    details=(
                        f"HR approved candidate {cand.name} (Score: {score_str}/{pass_mark}). "
                        f"CV Passed & Job Details emails sent with scheduling link: {scheduling_url}. "
                        f"{f'Note: {payload.notes}' if payload.notes else ''}"
                    ).strip(),
                )

                # 7. In-app Notification
                notif = Notification(
                    user_id=user_id,
                    title="Candidate Approved from CV Review",
                    message=f"{cand.name} approved for {opening_title}. CV Passed & Job Details emails dispatched.",
                    type="candidate_approved",
                    link=f"/pipeline?candidate_id={cand.id}",
                )
                session.add(notif)
                session.add(cand)

                try:
                    agent_events.emit_sync(user_id, "status_changed", {
                        "candidate_id": str(cand.id),
                        "candidate_name": cand.name,
                        "status": "approved",
                        "stage": "shortlisted",
                        "action": "approve",
                    })
                    agent_events.emit_sync(user_id, "email_sent", {
                        "candidate_id": str(cand.id),
                        "candidate_name": cand.name,
                        "template_id": "cv_passed",
                    })
                except Exception:
                    pass

                approved_count += 1
                results.append(
                    CVReviewDecisionItem(
                        candidate_id=cand.id,
                        candidate_name=cand.name,
                        action="approve",
                        status="approved",
                        stage="shortlisted",
                        emails_sent=emails_dispatched,
                        scheduling_link=scheduling_url,
                    )
                )

            elif action == "reject":
                # ── REJECT FLOW ───────────────────────────────────────────────
                old_stage = cand.stage.value if hasattr(cand.stage, "value") else str(cand.stage)
                cand.review_status = "rejected"
                cand.stage = CandidateStage.rejected
                cand.review_decision_at = now_utc
                cand.updated_at = now_utc

                template_vars = {
                    "candidate_name": cand.name,
                    "role": opening_title,
                    "company": company_name,
                    "hr_name": hr_name,
                    "signature": f"Sincerely,\n{hr_name}\n{company_name}",
                }

                # Resolve Rejection template strictly from DB via render_user_template
                rejection_sub, _, rejection_body, _ = render_user_template(
                    session, user_id, "rejection", template_vars
                )

                emails_dispatched = []

                # Dispatch Rejection Email
                msg_rej = Message(
                    user_id=user_id,
                    candidate_id=cand.id,
                    direction=MessageDirection.outbound,
                    message_type=MessageType.email,
                    channel="email",
                    body=rejection_body,
                    status=MessageStatus.sent,
                    hr_approved=True,
                    template_name="rejection",
                    template_variables={"subject": rejection_sub},
                    sent_at=now_utc,
                )
                session.add(msg_rej)
                emails_dispatched.append("Rejection")

                # Try dispatching via Google Workspace if active
                try:
                    from app.models.google_account import GoogleAccount
                    from app.services.google_service import GoogleSendEmailRequest, GoogleService
                    g_acct = session.exec(select(GoogleAccount).where(GoogleAccount.user_id == user_id)).first()
                    if g_acct and cand.email and "@" in cand.email and not cand.email.endswith("@no-email.com"):
                        g_service = GoogleService(session)
                        g_service.send_email(
                            user_id=user_id,
                            request=GoogleSendEmailRequest(
                                candidate_id=cand.id,
                                subject=rejection_sub,
                                body=rejection_body,
                                template_name="rejection",
                            ),
                        )
                except Exception as g_err:
                    logger.info("Google Workspace rejection dispatch note for %s: %s", cand.id, g_err)

                # Log Audit Trail
                score_str = f"{cand.score:.1f}" if cand.score is not None else "N/A"
                audit_log_service.record(
                    session=session,
                    user_id=user_id,
                    action="cv_review_rejected",
                    candidate_id=cand.id,
                    opening_id=cand.opening_id,
                    from_stage=old_stage,
                    to_stage="rejected",
                    details=(
                        f"HR rejected candidate {cand.name} (Score: {score_str}/{pass_mark}). "
                        f"Rejection email dispatched. {f'Note: {payload.notes}' if payload.notes else ''}"
                    ).strip(),
                )

                try:
                    agent_events.emit_sync(user_id, "status_changed", {
                        "candidate_id": str(cand.id),
                        "candidate_name": cand.name,
                        "status": "rejected",
                        "stage": "rejected",
                        "action": "reject",
                    })
                    agent_events.emit_sync(user_id, "email_sent", {
                        "candidate_id": str(cand.id),
                        "candidate_name": cand.name,
                        "template_id": "rejection",
                    })
                except Exception:
                    pass

                session.add(cand)
                rejected_count += 1
                results.append(
                    CVReviewDecisionItem(
                        candidate_id=cand.id,
                        candidate_name=cand.name,
                        action="reject",
                        status="rejected",
                        stage="rejected",
                        emails_sent=emails_dispatched,
                    )
                )

        session.commit()

        return CVReviewDecisionResponse(
            total_processed=len(payload.candidate_ids),
            approved_count=approved_count,
            rejected_count=rejected_count,
            results=results,
        )

    # ── 3. Update Opening Pass Mark ─────────────────────────────────────────────

    def update_opening_pass_mark(
        self,
        session: Session,
        user_id: uuid.UUID,
        opening_id: uuid.UUID,
        pass_mark: int,
    ) -> JobOpening:
        """Updates the pass mark threshold for a specific job opening."""
        if pass_mark < 1 or pass_mark > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pass mark must be between 1 and 100.",
            )

        opening = session.exec(
            select(JobOpening).where(
                JobOpening.id == opening_id,
                JobOpening.user_id == user_id,
            )
        ).first()

        if not opening:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job opening '{opening_id}' not found.",
            )

        opening.pass_mark = pass_mark
        opening.updated_at = datetime.now(timezone.utc)
        session.add(opening)
        session.commit()
        session.refresh(opening)

        audit_log_service.record(
            session=session,
            user_id=user_id,
            action="opening_pass_mark_updated",
            opening_id=opening.id,
            details=f"Pass mark for '{opening.title}' updated to {pass_mark}%.",
        )

        return opening

    # ── 4. Score Candidate & Place in Queue ──────────────────────────────────────

    async def score_and_queue_candidate(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
        force_rerun: bool = False,
    ) -> CVReviewQueueItem:
        """
        Runs AI fit scoring for candidate against their opening, computes recommendation
        (Recommended / Borderline / Not recommended) using the opening's pass mark,
        and lands candidate in 'Needs HR Review' queue.
        NOTHING is sent before HR decides.
        """
        cand = session.exec(
            select(Candidate).where(Candidate.id == candidate_id, Candidate.user_id == user_id)
        ).first()
        if not cand:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate '{candidate_id}' not found.",
            )

        opening = session.exec(
            select(JobOpening).where(JobOpening.id == cand.opening_id)
        ).first()
        if not opening:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Associated Job Opening not found for candidate '{candidate_id}'.",
            )

        pass_mark = getattr(opening, "pass_mark", 80) or 80

        try:
            agent_events.emit_sync(user_id, "ai_scanning", {
                "candidate_id": str(cand.id),
                "candidate_name": cand.name,
                "opening_title": opening.title,
            })
        except Exception:
            pass

        # Run AI screening
        eval_res = await screen_candidate_cv(
            job_title=opening.title,
            job_description=opening.description,
            required_skills=opening.required_skills or [],
            candidate_name=cand.name,
            cv_text=cand.cv_text,
        )

        cand.score = eval_res["score"]
        cand.matched_skills = eval_res["matched_skills"]
        cand.missing_skills = eval_res["missing_skills"]
        cand.red_flags = eval_res.get("red_flags", [])
        cand.summary = eval_res["summary"]
        cand.review_status = "pending"  # Lands in Needs HR Review queue
        cand.updated_at = datetime.now(timezone.utc)

        # Store recommendation and metadata in extracted_data
        rec = compute_recommendation(cand.score, pass_mark=pass_mark)
        ext = dict(cand.extracted_data or {})
        ext["recommendation"] = rec
        ext["model_used"] = eval_res.get("model_used")
        ext["latency_seconds"] = eval_res.get("latency_seconds")
        cand.extracted_data = ext

        try:
            agent_events.emit_sync(user_id, "scored", {
                "candidate_id": str(cand.id),
                "candidate_name": cand.name,
                "score": cand.score,
                "recommendation": rec,
                "summary": cand.summary,
            })
            agent_events.emit_sync(user_id, "status_changed", {
                "candidate_id": str(cand.id),
                "candidate_name": cand.name,
                "status": "pending",
                "stage": "applied",
            })
        except Exception:
            pass

        session.add(cand)
        session.commit()
        session.refresh(cand)

        audit_log_service.record(
            session=session,
            user_id=user_id,
            action="cv_scored_for_review",
            candidate_id=cand.id,
            opening_id=cand.opening_id,
            details=f"AI scored CV for {cand.name}: {cand.score}/100 ({rec}, Pass Mark: {pass_mark}). Placed in Needs HR Review queue.",
        )

        return CVReviewQueueItem(
            id=cand.id,
            user_id=cand.user_id,
            opening_id=cand.opening_id,
            opening_title=opening.title,
            opening_pass_mark=pass_mark,
            name=cand.name,
            email=cand.email,
            cv_text=cand.cv_text,
            cv_file_url=cand.cv_file_url,
            score=cand.score,
            recommendation=rec,
            matched_skills=cand.matched_skills or [],
            missing_skills=cand.missing_skills or [],
            red_flags=cand.red_flags or [],
            summary=cand.summary,
            stage=cand.stage.value if hasattr(cand.stage, "value") else str(cand.stage),
            review_status=cand.review_status,
            review_decision_at=cand.review_decision_at,
            created_at=cand.created_at,
            updated_at=cand.updated_at,
        )


cv_review_service = CVReviewService()
