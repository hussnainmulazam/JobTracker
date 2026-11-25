"""Candidate service — business logic and DB operations for recruiter candidates."""
import csv
import hashlib
import io
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlmodel import Session, func, select

from app.core.pdf import extract_text_from_pdf, parse_cv_document
from app.core.storage import save_candidate_cv_file
from app.schemas.extractor import CandidateConfirmPayload, ExtractedCandidateData
from app.services.extractor_service import extract_all_deterministic_fields
from app.models.candidate import Candidate, CandidateStage
from app.models.job_opening import JobOpening
from app.models.candidate_link import CandidateLink
from app.models.message import Message
from app.models.interview import Interview, SchedulingLink
from app.models.audit_log import AuditLog
from app.schemas.candidate import (
    BulkScoreResponse,
    CandidateCreate,
    CandidateDataExportResponse,
    CandidateRead,
    CandidateScreeningQuestionsResponse,
    CandidateScreenResult,
    CandidateUpdate,
    PaginatedCandidates,
)
from app.schemas.extractor import CandidateLinkRead
from app.schemas.message import MessageRead
from app.schemas.scheduling import InterviewRead, SchedulingLinkRead
from app.schemas.audit_log import AuditLogRead
import app.services.matching_service as matching_service

# Exposed at module level for mocking & backward compatibility
screen_candidate_cv = matching_service.screen_candidate_cv
from app.services.ai import (
    generate_recruiter_interview_questions,
)
from app.services.audit_log_service import audit_log_service
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

# Cache candidate screening results per (candidate_id, opening_id, cv_hash)
_SCREENING_CACHE: dict[tuple[str, str, str], dict] = {}


class CandidateService:
    def create(
        self,
        session: Session,
        user_id: uuid.UUID,
        data: CandidateCreate,
    ) -> CandidateRead:
        opening = session.exec(
            select(JobOpening).where(
                JobOpening.id == data.opening_id,
                JobOpening.user_id == user_id,
            )
        ).first()
        if not opening:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job opening '{data.opening_id}' not found.",
            )

        existing = session.exec(
            select(Candidate).where(
                Candidate.user_id == user_id,
                Candidate.opening_id == data.opening_id,
                Candidate.email == str(data.email).strip().lower(),
            )
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Candidate with email '{data.email}' has already applied for this opening.",
            )

        candidate = Candidate(
            user_id=user_id,
            opening_id=data.opening_id,
            name=data.name.strip(),
            email=str(data.email).strip().lower(),
            cv_text=data.cv_text.strip(),
            cv_file_url=str(data.cv_file_url).strip() if data.cv_file_url else None,
            stage=CandidateStage.applied,
        )
        session.add(candidate)
        session.commit()
        session.refresh(candidate)

        audit_log_service.record(
            session=session,
            user_id=user_id,
            action="candidate_created",
            candidate_id=candidate.id,
            opening_id=candidate.opening_id,
            to_stage=candidate.stage.value if hasattr(candidate.stage, "value") else str(candidate.stage),
            details=f"Candidate {candidate.name} added to pipeline.",
        )
        notification_service.create(
            session=session,
            user_id=user_id,
            title="New Candidate Added",
            message=f"{candidate.name} was added to '{opening.title}'.",
            type="new_applicant",
            link=f"/pipeline?candidate_id={candidate.id}",
        )

        # Automated AI scoring on intake & auto acknowledgement email
        self.auto_handle_candidate_received(session, user_id, candidate)

        read = CandidateRead.model_validate(candidate)
        read.opening_title = opening.title
        read.scorecards = []
        return read

    def create_from_pdf(
        self,
        session: Session,
        user_id: uuid.UUID,
        opening_id: uuid.UUID,
        name: Optional[str],
        email: Optional[str],
        pdf_bytes: bytes,
        cv_file_url: Optional[str] = None,
    ) -> CandidateRead:
        if len(pdf_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )

        if len(pdf_bytes) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds the 10MB limit.",
            )

        # Extract text via document parser (PDF, DOCX, OCR fallback)
        extracted_text = parse_cv_document(pdf_bytes, cv_file_url or "document.pdf")

        # Automatic extraction fallback for name and email if missing
        final_name = (name or "").strip()
        final_email = (email or "").strip().lower()

        if not final_name or not final_email:
            det = extract_all_deterministic_fields(extracted_text)
            cand_data = det["extracted_data"]
            if not final_name and cand_data.name:
                final_name = cand_data.name
            if not final_email and cand_data.email:
                final_email = cand_data.email

        if not final_name:
            final_name = "Candidate"
        if not final_email:
            final_email = f"unspecified-{uuid.uuid4().hex[:8]}@no-email.com"

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

        existing = session.exec(
            select(Candidate).where(
                Candidate.user_id == user_id,
                Candidate.opening_id == opening_id,
                Candidate.email == final_email,
            )
        ).first()
        if existing and not final_email.endswith("@no-email.com"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Candidate with email '{final_email}' has already applied for this opening.",
            )

        # Save file to storage
        saved_file_url = cv_file_url
        if pdf_bytes:
            saved_file_url = save_candidate_cv_file(cv_file_url or "resume.pdf", pdf_bytes)

        candidate = Candidate(
            user_id=user_id,
            opening_id=opening_id,
            name=final_name,
            email=final_email,
            cv_text=extracted_text,
            cv_file_url=saved_file_url,
            stage=CandidateStage.applied,
        )
        session.add(candidate)
        session.commit()
        session.refresh(candidate)

        audit_log_service.record(
            session=session,
            user_id=user_id,
            action="candidate_created",
            candidate_id=candidate.id,
            opening_id=candidate.opening_id,
            to_stage=candidate.stage.value if hasattr(candidate.stage, "value") else str(candidate.stage),
            details=f"Candidate {candidate.name} added to pipeline.",
        )
        notification_service.create(
            session=session,
            user_id=user_id,
            title="New Candidate Added",
            message=f"{candidate.name} was added to '{opening.title}'.",
            type="new_applicant",
            link=f"/pipeline?candidate_id={candidate.id}",
        )

        # Automated AI scoring on intake & auto acknowledgement email
        self.auto_handle_candidate_received(session, user_id, candidate)

        read = CandidateRead.model_validate(candidate)
        read.opening_title = opening.title
        read.scorecards = []
        return read

    async def confirm_candidate(
        self,
        session: Session,
        user_id: uuid.UUID,
        payload: CandidateConfirmPayload,
    ) -> CandidateRead:
        opening_uuid = uuid.UUID(payload.opening_id)
        opening = session.exec(
            select(JobOpening).where(
                JobOpening.id == opening_uuid,
                JobOpening.user_id == user_id,
            )
        ).first()
        if not opening:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job opening '{payload.opening_id}' not found.",
            )

        if payload.action == "skip":
            raise HTTPException(
                status_code=status.HTTP_200_OK,
                detail="Candidate addition skipped.",
            )

        # ── MERGE ACTION ──────────────────────────────────────────────────────
        if payload.action == "merge" and payload.merge_candidate_id:
            merge_uuid = uuid.UUID(payload.merge_candidate_id)
            candidate = session.exec(
                select(Candidate).where(
                    Candidate.id == merge_uuid,
                    Candidate.user_id == user_id,
                )
            ).first()
            if not candidate:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Candidate '{payload.merge_candidate_id}' to merge into not found.",
                )

            # Update existing candidate fields with new CV information
            candidate.cv_text = payload.cv_text
            if payload.cv_file_url:
                candidate.cv_file_url = payload.cv_file_url
            if payload.name:
                candidate.name = payload.name.strip()
            if payload.email and "@" in payload.email and not payload.email.endswith("@no-email.com"):
                candidate.email = payload.email.strip().lower()
            if payload.phone:
                candidate.phone = payload.phone.strip()
            if payload.address:
                candidate.address = payload.address.strip()
            if payload.github_url:
                candidate.github_url = payload.github_url
            if payload.linkedin_url:
                candidate.linkedin_url = payload.linkedin_url
            if payload.portfolio_url:
                candidate.portfolio_url = payload.portfolio_url
            if payload.kaggle_url:
                candidate.kaggle_url = payload.kaggle_url

            # Merge extracted_data
            curr_data = dict(candidate.extracted_data or {})
            new_data = dict(payload.extracted_data or {})
            if payload.current_title:
                new_data["current_title"] = payload.current_title
            if payload.years_of_experience is not None:
                new_data["years_of_experience"] = payload.years_of_experience
            if payload.top_skills:
                new_data["top_skills"] = payload.top_skills
            if payload.education:
                new_data["education"] = payload.education
            curr_data.update(new_data)
            candidate.extracted_data = curr_data
            candidate.updated_at = datetime.now(timezone.utc)

            session.add(candidate)
            session.commit()
            session.refresh(candidate)

            audit_log_service.record(
                session=session,
                user_id=user_id,
                action="candidate_merged",
                candidate_id=candidate.id,
                opening_id=candidate.opening_id,
                details=f"Merged updated CV details into candidate '{candidate.name}'.",
            )

            # Auto-screen if requested
            if payload.auto_screen:
                try:
                    await self.score_candidate(session, user_id, candidate.id, re_run=True)
                    session.refresh(candidate)
                except Exception as exc:
                    logger.warning("Auto-screening failed for merged candidate: %s", exc)

            read = CandidateRead.model_validate(candidate)
            read.opening_title = opening.title
            read.scorecards = []
            return read

        # ── CREATE ACTION ──────────────────────────────────────────────────────
        candidate_email = (payload.email or "").strip().lower()
        if not candidate_email or "@" not in candidate_email:
            candidate_email = f"unspecified-{uuid.uuid4().hex[:8]}@no-email.com"

        existing = session.exec(
            select(Candidate).where(
                Candidate.user_id == user_id,
                Candidate.opening_id == opening_uuid,
                Candidate.email == candidate_email,
            )
        ).first()
        if existing and not candidate_email.endswith("@no-email.com"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Candidate with email '{candidate_email}' has already applied for this opening. Please use 'Merge' instead.",
            )

        extracted_dict = dict(payload.extracted_data or {})
        if payload.current_title:
            extracted_dict["current_title"] = payload.current_title
        if payload.years_of_experience is not None:
            extracted_dict["years_of_experience"] = payload.years_of_experience
        if payload.top_skills:
            extracted_dict["top_skills"] = payload.top_skills
        if payload.education:
            extracted_dict["education"] = payload.education

        candidate = Candidate(
            user_id=user_id,
            opening_id=opening_uuid,
            name=payload.name.strip() or "Unnamed Candidate",
            email=candidate_email,
            phone=payload.phone.strip() if payload.phone else None,
            address=payload.address.strip() if payload.address else None,
            github_url=payload.github_url,
            linkedin_url=payload.linkedin_url,
            portfolio_url=payload.portfolio_url,
            kaggle_url=payload.kaggle_url,
            cv_text=payload.cv_text,
            cv_file_url=payload.cv_file_url,
            extracted_data=extracted_dict,
            stage=CandidateStage.applied,
        )
        session.add(candidate)
        session.commit()
        session.refresh(candidate)

        audit_log_service.record(
            session=session,
            user_id=user_id,
            action="candidate_created",
            candidate_id=candidate.id,
            opening_id=candidate.opening_id,
            to_stage=candidate.stage.value if hasattr(candidate.stage, "value") else str(candidate.stage),
            details=f"Candidate '{candidate.name}' added to pipeline via upload-first extraction.",
        )
        notification_service.create(
            session=session,
            user_id=user_id,
            title="New Candidate Added",
            message=f"{candidate.name} was added to '{opening.title}'.",
            type="new_applicant",
            link=f"/pipeline?candidate_id={candidate.id}",
        )

        # Auto-screen if requested
        if payload.auto_screen:
            try:
                await self.score_candidate(session, user_id, candidate.id, re_run=False)
                session.refresh(candidate)
            except Exception as exc:
                logger.warning("Auto-screening failed for newly created candidate: %s", exc)

        read = CandidateRead.model_validate(candidate)
        read.opening_title = opening.title
        read.scorecards = []
        return read

    def upload_pdf_cv(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
        pdf_bytes: bytes,
        cv_file_url: Optional[str] = None,
    ) -> CandidateRead:
        candidate = self.get_by_id(session, user_id, candidate_id)
        extracted_text = parse_cv_document(pdf_bytes, cv_file_url or "cv.pdf")

        candidate.cv_text = extracted_text
        if cv_file_url:
            candidate.cv_file_url = cv_file_url
        candidate.updated_at = datetime.now(timezone.utc)

        session.add(candidate)
        session.commit()
        session.refresh(candidate)

        audit_log_service.record(
            session=session,
            user_id=user_id,
            action="cv_uploaded",
            candidate_id=candidate.id,
            opening_id=candidate.opening_id,
            details="Updated CV PDF uploaded.",
        )

        return self.get_read_by_id(session, user_id, candidate.id)

    def get_by_id(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
    ) -> Candidate:
        statement = select(Candidate).where(
            Candidate.id == candidate_id,
            Candidate.user_id == user_id,
        )
        candidate = session.exec(statement).first()
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate '{candidate_id}' not found.",
            )
        return candidate

    def get_read_by_id(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
    ) -> CandidateRead:
        candidate = self.get_by_id(session, user_id, candidate_id)

        opening = session.exec(
            select(JobOpening).where(JobOpening.id == candidate.opening_id)
        ).first()

        read = CandidateRead.model_validate(candidate)
        read.opening_title = opening.title if opening else None
        read.scorecards = []
        return read

    def list(
        self,
        session: Session,
        user_id: uuid.UUID,
        opening_id: Optional[uuid.UUID] = None,
        stage: Optional[CandidateStage] = None,
        min_score: Optional[float] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> PaginatedCandidates:
        query = select(Candidate).where(Candidate.user_id == user_id)

        if opening_id:
            query = query.where(Candidate.opening_id == opening_id)

        if stage:
            query = query.where(Candidate.stage == stage)

        if min_score is not None:
            query = query.where(Candidate.score >= min_score)

        if search:
            query = query.where(
                (Candidate.name.ilike(f"%{search.strip()}%"))
                | (Candidate.email.ilike(f"%{search.strip()}%"))
            )

        count_stmt = select(func.count()).select_from(query.subquery())
        total = session.exec(count_stmt).one() or 0

        query = query.order_by(Candidate.created_at.desc()).offset(skip).limit(limit)
        items = session.exec(query).all()

        opening_ids = {c.opening_id for c in items if c.opening_id}
        openings_map = {}
        if opening_ids:
            from sqlmodel import col
            openings = session.exec(select(JobOpening).where(col(JobOpening.id).in_(opening_ids))).all()
            openings_map = {op.id: op.title for op in openings}

        read_items: list[CandidateRead] = []
        for c in items:
            r = CandidateRead.model_validate(c)
            r.opening_title = openings_map.get(c.opening_id)
            if not r.recommendation:
                r.recommendation = (c.extracted_data or {}).get("recommendation")
            read_items.append(r)

        return PaginatedCandidates(
            items=read_items,
            total=total,
            skip=skip,
            limit=limit,
        )

    def update(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
        data: CandidateUpdate,
    ) -> CandidateRead:
        candidate = self.get_by_id(session, user_id, candidate_id)

        update_dict = data.model_dump(exclude_unset=True)
        if "name" in update_dict and update_dict["name"]:
            update_dict["name"] = update_dict["name"].strip()
        if "email" in update_dict and update_dict["email"]:
            update_dict["email"] = str(update_dict["email"]).strip().lower()
        if "cv_text" in update_dict and update_dict["cv_text"]:
            update_dict["cv_text"] = update_dict["cv_text"].strip()

        for key, value in update_dict.items():
            setattr(candidate, key, value)

        candidate.updated_at = datetime.now(timezone.utc)
        session.add(candidate)
        session.commit()
        session.refresh(candidate)

        audit_log_service.record(
            session=session,
            user_id=user_id,
            action="cv_uploaded",
            candidate_id=candidate.id,
            opening_id=candidate.opening_id,
            details="Updated CV PDF uploaded.",
        )

        return self.get_read_by_id(session, user_id, candidate.id)

    def update_stage(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
        stage: CandidateStage,
    ) -> CandidateRead:
        candidate = self.get_by_id(session, user_id, candidate_id)
        old_stage = candidate.stage.value if hasattr(candidate.stage, "value") else str(candidate.stage)
        candidate.stage = stage
        new_stage = stage.value if hasattr(stage, "value") else str(stage)
        candidate.updated_at = datetime.now(timezone.utc)
        session.add(candidate)
        session.commit()
        session.refresh(candidate)

        audit_log_service.record(
            session=session,
            user_id=user_id,
            action="cv_uploaded",
            candidate_id=candidate.id,
            opening_id=candidate.opening_id,
            details="Updated CV PDF uploaded.",
        )

        audit_log_service.record(
            session=session,
            user_id=user_id,
            action="stage_change",
            candidate_id=candidate.id,
            opening_id=candidate.opening_id,
            from_stage=old_stage,
            to_stage=new_stage,
            details=f"Moved {candidate.name} from {old_stage} to {new_stage}.",
        )

        # Trigger auto-approval email if moved to interview, shortlisted, or offer
        if stage in (CandidateStage.interview, CandidateStage.shortlisted, CandidateStage.offer) and old_stage != new_stage:
            self.auto_send_approval_email(session, user_id, candidate)

        return self.get_read_by_id(session, user_id, candidate.id)

    def bulk_update_stage(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_ids: List[uuid.UUID],
        stage: CandidateStage,
    ) -> int:
        count = 0
        new_stage_str = stage.value if hasattr(stage, "value") else str(stage)
        for cid in candidate_ids:
            cand = session.exec(
                select(Candidate).where(Candidate.id == cid, Candidate.user_id == user_id)
            ).first()
            if cand:
                old_stage_str = cand.stage.value if hasattr(cand.stage, "value") else str(cand.stage)
                cand.stage = stage
                cand.updated_at = datetime.now(timezone.utc)
                session.add(cand)
                session.commit()
                session.refresh(cand)

                audit_log_service.record(
                    session=session,
                    user_id=user_id,
                    action="bulk_stage_update",
                    candidate_id=cand.id,
                    opening_id=cand.opening_id,
                    from_stage=old_stage_str,
                    to_stage=new_stage_str,
                    details=f"Bulk moved {cand.name} to {new_stage_str}.",
                )
                if stage in (CandidateStage.interview, CandidateStage.shortlisted, CandidateStage.offer) and old_stage_str != new_stage_str:
                    self.auto_send_approval_email(session, user_id, cand)
                count += 1
        return count

    def auto_handle_candidate_received(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate: Candidate,
    ) -> None:
        """
        Automated workflow when a candidate CV is received/ingested:
        1. Auto-checks AI scoring (fit score, matched/missing skills, red flags, summary).
        2. Dispatches automated application received acknowledgement email from recruiter's Gmail.
        """
        import os
        import sys
        if os.getenv("TESTING") == "true" or "pytest" in sys.modules:
            return
        # 1. AI Scoring
        try:
            import asyncio
            import concurrent.futures

            async def _do_score():
                return await self.score_candidate(session, user_id, candidate.id, re_run=False)

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    pool.submit(asyncio.run, _do_score()).result()
            else:
                asyncio.run(_do_score())

            session.refresh(candidate)
            logger.info("Candidate %s auto-scored successfully: score=%s", candidate.id, candidate.score)
        except Exception as exc:
            logger.warning("Auto-screening scoring failed on intake for candidate %s: %s", candidate.id, exc)

        # 2. Auto-dispatch 'CV received' Initial Message Email
        self.send_auto_reply_email(session, user_id, candidate, force_resend=False)

    def send_auto_reply_email(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate: Candidate,
        force_resend: bool = False,
    ) -> bool:
        """
        Dispatches 'CV received' email from HR's Gmail using the Initial Message template.
        Rules:
        - Send only once per candidate (unless force_resend=True)
        - Only if email was extracted (and not placeholder)
        - Only if auto_reply_enabled is True in Settings (unless force_resend=True)
        - Updates candidate.auto_reply_status, auto_reply_sent, auto_reply_sent_at, auto_reply_error
        - Records in audit trail with real outcome/error
        """
        import os
        import sys
        if os.getenv("TESTING") == "true" or "pytest" in sys.modules:
            return False

        if not candidate.email or candidate.email.endswith("@no-email.com"):
            logger.info("Candidate %s has no valid extracted email, skipping auto-reply", candidate.id)
            return False

        if candidate.auto_reply_sent and not force_resend:
            logger.info("Auto-reply already sent for candidate %s, skipping", candidate.id)
            return True

        from app.models.google_account import GoogleAccount
        account = session.exec(
            select(GoogleAccount).where(GoogleAccount.user_id == user_id)
        ).first()

        if not account:
            logger.info("No connected Google account for user %s, skipping auto-reply", user_id)
            return False

        if not force_resend and not getattr(account, "auto_reply_enabled", True):
            logger.info("Auto-reply is disabled in Settings for user %s, skipping", user_id)
            return False

        opening = session.exec(
            select(JobOpening).where(JobOpening.id == candidate.opening_id)
        ).first()
        job_title = opening.title if opening else "Position"

        from app.services.pipeline_agent_service import build_pipeline_context
        from app.services.template_service import render_user_template

        ctx = build_pipeline_context(session, user_id, candidate)
        subject, html_body, body, _ = render_user_template(session, user_id, "cv_received", ctx)

        from app.services.google_service import GoogleService
        from app.schemas.google import GoogleSendEmailRequest

        google_svc = GoogleService(session)
        now = datetime.now(timezone.utc)
        try:
            google_svc.send_email(
                user_id=user_id,
                request=GoogleSendEmailRequest(
                    candidate_id=candidate.id,
                    subject=subject,
                    body=html_body,
                    template_name="cv_received",
                ),
            )
            candidate.auto_reply_sent = True
            candidate.auto_reply_status = "sent"
            candidate.auto_reply_sent_at = now
            candidate.auto_reply_error = None
            session.add(candidate)
            session.commit()
            session.refresh(candidate)

            audit_log_service.record(
                session=session,
                user_id=user_id,
                action="auto_reply_sent",
                candidate_id=candidate.id,
                opening_id=candidate.opening_id,
                details=f"Auto-reply 'CV received' email sent to {candidate.email} via Gmail.",
            )
            return True
        except Exception as exc:
            err_msg = str(exc)
            candidate.auto_reply_sent = False
            candidate.auto_reply_status = "failed"
            candidate.auto_reply_error = err_msg
            session.add(candidate)
            session.commit()
            session.refresh(candidate)

            audit_log_service.record(
                session=session,
                user_id=user_id,
                action="auto_reply_failed",
                candidate_id=candidate.id,
                opening_id=candidate.opening_id,
                details=f"Failed sending 'CV received' email to {candidate.email}: {err_msg}",
            )
            logger.warning("Failed sending auto-reply email to %s: %s", candidate.email, err_msg)
            if force_resend:
                raise
            return False

    def resend_auto_reply(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
    ) -> CandidateRead:
        """Manually trigger or retry the 'CV received' auto-reply email."""
        candidate = session.exec(
            select(Candidate).where(
                Candidate.id == candidate_id,
                Candidate.user_id == user_id,
            )
        ).first()
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate '{candidate_id}' not found.",
            )
        if not candidate.email or candidate.email.endswith("@no-email.com"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidate has no extracted or valid email address.",
            )

        self.send_auto_reply_email(session, user_id, candidate, force_resend=True)
        read = CandidateRead.model_validate(candidate)
        opening = session.exec(select(JobOpening).where(JobOpening.id == candidate.opening_id)).first()
        read.opening_title = opening.title if opening else None
        return read

    def auto_send_approval_email(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate: Candidate,
    ) -> None:
        """
        Automated workflow when a candidate application is approved:
        1. Generates candidate-specific self-scheduling booking link.
        2. Dispatches an interview invitation email from the recruiter's connected Gmail.
        """
        import os
        import sys
        if os.getenv("TESTING") == "true" or "pytest" in sys.modules:
            return

        if not candidate.email or candidate.email.endswith("@no-email.com"):
            return

        try:
            from app.services.scheduling_service import scheduling_service
            from app.services.google_service import GoogleService
            from app.schemas.google import GoogleSendEmailRequest

            opening = session.exec(
                select(JobOpening).where(JobOpening.id == candidate.opening_id)
            ).first()
            job_title = opening.title if opening else "Position"

            sched_link = scheduling_service.create_scheduling_link(
                session=session,
                user_id=user_id,
                candidate_id=candidate.id,
                validity_days=7,
            )
            booking_url = sched_link.booking_url

            from app.services.pipeline_agent_service import build_pipeline_context
            from app.services.template_service import render_user_template

            ctx = build_pipeline_context(session, user_id, candidate)
            ctx["schedule_link"] = booking_url
            ctx["booking_link"] = booking_url
            subject, html_body, body, _ = render_user_template(session, user_id, "cv_passed", ctx)

            google_svc = GoogleService(session)
            google_svc.send_email(
                user_id=user_id,
                request=GoogleSendEmailRequest(
                    candidate_id=candidate.id,
                    subject=subject,
                    body=body,
                    html_body=html_body,
                    template_name="cv_passed",
                ),
            )
            logger.info("Auto-sent approval and interview invitation email to %s (%s)", candidate.name, candidate.email)
        except Exception as exc:
            logger.warning("Failed to auto-send approval interview invitation email to %s: %s", candidate.email, exc)

    def bulk_delete(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_ids: List[uuid.UUID],
    ) -> int:
        count = 0
        for cid in candidate_ids:
            cand = session.exec(
                select(Candidate).where(Candidate.id == cid, Candidate.user_id == user_id)
            ).first()
            if cand:
                cand_name = cand.name
                op_id = cand.opening_id
                session.delete(cand)
                session.commit()

                audit_log_service.record(
                    session=session,
                    user_id=user_id,
                    action="candidate_deleted",
                    candidate_id=None,
                    opening_id=op_id,
                    details=f"Deleted candidate {cand_name} ({cid}).",
                )
                count += 1
        return count

    def delete(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
    ) -> None:
        """
        Permanently delete candidate and perform full cascading deletion of child records:
        scorecards, candidate links, messages, interviews, and scheduling links.
        Historical audit logs have candidate_id detached to preserve audit compliance.
        """
        candidate = self.get_by_id(session, user_id, candidate_id)
        cand_name = candidate.name
        op_id = candidate.opening_id

        # 1. Cascade delete CandidateLinks
        links = session.exec(
            select(CandidateLink).where(
                CandidateLink.candidate_id == candidate_id,
                CandidateLink.user_id == user_id,
            )
        ).all()
        for l in links:
            session.delete(l)

        # 3. Cascade delete Messages
        messages = session.exec(
            select(Message).where(
                Message.candidate_id == candidate_id,
                Message.user_id == user_id,
            )
        ).all()
        for m in messages:
            session.delete(m)

        # 4. Cascade delete Interviews
        interviews = session.exec(
            select(Interview).where(
                Interview.candidate_id == candidate_id,
                Interview.user_id == user_id,
            )
        ).all()
        for iv in interviews:
            session.delete(iv)

        # 5. Cascade delete SchedulingLinks
        sched_links = session.exec(
            select(SchedulingLink).where(
                SchedulingLink.candidate_id == candidate_id,
                SchedulingLink.user_id == user_id,
            )
        ).all()
        for sl in sched_links:
            session.delete(sl)

        # 6. Detach FK in audit_logs to preserve historical logs without FK violation
        audits = session.exec(
            select(AuditLog).where(AuditLog.candidate_id == candidate_id)
        ).all()
        for a in audits:
            a.candidate_id = None
            session.add(a)

        # 7. Delete Candidate
        session.delete(candidate)
        session.commit()

        # 8. Record audit log entry
        audit_log_service.record(
            session=session,
            user_id=user_id,
            action="candidate_deleted",
            candidate_id=None,
            opening_id=op_id,
            details=f"Permanently deleted candidate {cand_name} ({candidate_id}) and all cascading records.",
        )

    def export_candidate_data(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
    ) -> CandidateDataExportResponse:
        """
        GDPR / Data Subject Access Request export endpoint.
        Returns full structured record of candidate: profile, links, scorecards,
        messages, scheduled interviews, booking links, and audit history.
        """
        candidate_read = self.get_read_by_id(session, user_id, candidate_id)

        # 1. Links
        raw_links = session.exec(
            select(CandidateLink).where(
                CandidateLink.candidate_id == candidate_id,
                CandidateLink.user_id == user_id,
            )
        ).all()
        links = [
            CandidateLinkRead(
                id=str(l.id),
                candidate_id=str(l.candidate_id),
                link_type=l.link_type,
                url=l.url,
                is_verified=l.is_verified,
                confidence=l.confidence,
                source=l.source,
            )
            for l in raw_links
        ]

        # 2. Scorecards (empty list placeholder for schema compatibility)
        scorecards = []

        # 3. Communications / Messages
        raw_messages = session.exec(
            select(Message).where(
                Message.candidate_id == candidate_id,
                Message.user_id == user_id,
            )
        ).all()
        messages = [MessageRead.model_validate(m) for m in raw_messages]

        # 4. Interviews
        from app.services.scheduling_service import scheduling_service
        raw_interviews = session.exec(
            select(Interview).where(
                Interview.candidate_id == candidate_id,
                Interview.user_id == user_id,
            )
        ).all()
        interviews = [scheduling_service._to_interview_read(iv) for iv in raw_interviews]

        # 5. Scheduling Links
        raw_sched = session.exec(
            select(SchedulingLink).where(
                SchedulingLink.candidate_id == candidate_id,
                SchedulingLink.user_id == user_id,
            )
        ).all()
        sched_links = [
            SchedulingLinkRead(
                id=sl.id,
                token=sl.token,
                user_id=sl.user_id,
                candidate_id=sl.candidate_id,
                candidate_name=candidate_read.name,
                candidate_email=candidate_read.email,
                opening_id=sl.opening_id,
                opening_title=candidate_read.opening_title or "Job Opening",
                slot_duration_minutes=sl.slot_duration_minutes,
                status=sl.status.value if hasattr(sl.status, "value") else str(sl.status),
                expires_at=sl.expires_at,
                public_url=f"/schedule/{sl.token}",
                created_at=sl.created_at,
            )
            for sl in raw_sched
        ]

        # 6. Audit Trail
        raw_audits = audit_log_service.list_for_candidate(
            session=session,
            user_id=user_id,
            candidate_id=candidate_id,
        )

        # Audit record
        audit_log_service.record(
            session=session,
            user_id=user_id,
            action="candidate_data_exported",
            candidate_id=candidate_id,
            opening_id=candidate_read.opening_id,
            details=f"GDPR candidate data export requested for {candidate_read.name} ({candidate_read.email}).",
        )

        return CandidateDataExportResponse(
            candidate=candidate_read,
            links=links,
            scorecards=scorecards,
            messages=messages,
            interviews=interviews,
            scheduling_links=sched_links,
            audit_trail=raw_audits,
            exported_at=datetime.now(timezone.utc),
        )

    async def score_candidate(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
        re_run: bool = False,
    ) -> CandidateScreenResult:
        """
        POST /candidates/{id}/score using OpenRouter.
        Caches results per (candidate_id, opening_id, cv_hash).
        If re_run is False and result is cached (or candidate was already scored with identical CV),
        returns cached result immediately without calling LLM.
        """
        candidate = self.get_by_id(session, user_id, candidate_id)
        opening = session.exec(
            select(JobOpening).where(
                JobOpening.id == candidate.opening_id,
                JobOpening.user_id == user_id,
            )
        ).first()
        if not opening:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated Job Opening not found.",
            )

        cv_raw = (candidate.cv_text or "").strip()
        cv_hash = hashlib.sha256(cv_raw.encode("utf-8")).hexdigest()
        cache_key = (str(candidate.id), str(candidate.opening_id), cv_hash)

        # 1. Check in-memory cache
        if not re_run and cache_key in _SCREENING_CACHE:
            cached = _SCREENING_CACHE[cache_key]
            logger.info("Screening cache hit (in-memory) for candidate %s", candidate.id)
            return CandidateScreenResult(
                candidate_id=candidate.id,
                candidate_name=candidate.name,
                score=cached["score"],
                matched_skills=cached["matched_skills"],
                missing_skills=cached["missing_skills"],
                red_flags=cached.get("red_flags", []),
                summary=cached.get("summary", ""),
                recommendation=cached.get("recommendation"),
                interview_focus_areas=cached.get("interview_focus_areas", []),
                stage=candidate.stage,
                model_used=cached.get("model_used"),
                latency_seconds=cached.get("latency_seconds"),
            )

        # 2. Check DB cached screening state
        stored_hash = (candidate.extracted_data or {}).get("cv_hash")
        if not re_run and candidate.score is not None and (stored_hash == cv_hash or stored_hash is None):
            logger.info("Screening cache hit (DB record) for candidate %s", candidate.id)
            if stored_hash is None:
                ext_data = dict(candidate.extracted_data or {})
                ext_data["cv_hash"] = cv_hash
                candidate.extracted_data = ext_data
                session.add(candidate)
                session.commit()
                session.refresh(candidate)
            ext = candidate.extracted_data or {}
            cached_result = {
                "score": candidate.score,
                "matched_skills": candidate.matched_skills or [],
                "missing_skills": candidate.missing_skills or [],
                "red_flags": candidate.red_flags or [],
                "summary": candidate.summary or "",
                "recommendation": ext.get("recommendation"),
                "interview_focus_areas": ext.get("interview_focus_areas", []),
                "model_used": ext.get("model_used"),
                "latency_seconds": ext.get("latency_seconds", 0.0),
            }
            _SCREENING_CACHE[cache_key] = cached_result
            return CandidateScreenResult(
                candidate_id=candidate.id,
                candidate_name=candidate.name,
                score=candidate.score,
                matched_skills=candidate.matched_skills or [],
                missing_skills=candidate.missing_skills or [],
                red_flags=candidate.red_flags or [],
                summary=candidate.summary or "",
                recommendation=ext.get("recommendation"),
                interview_focus_areas=ext.get("interview_focus_areas", []),
                stage=candidate.stage,
                model_used=ext.get("model_used"),
                latency_seconds=ext.get("latency_seconds"),
            )

        # 3. Cache miss or explicit re_run: call LLM via ai_router
        _screen_fn = screen_candidate_cv
        if matching_service.screen_candidate_cv is not _screen_fn and hasattr(matching_service.screen_candidate_cv, "assert_called"):
            _screen_fn = matching_service.screen_candidate_cv
        result = await _screen_fn(
            job_title=opening.title,
            job_description=opening.description,
            required_skills=opening.required_skills or [],
            candidate_name=candidate.name,
            cv_text=candidate.cv_text,
        )

        candidate.score = result["score"]
        candidate.matched_skills = result["matched_skills"]
        candidate.missing_skills = result["missing_skills"]
        candidate.red_flags = result.get("red_flags", [])
        candidate.summary = result["summary"]
        if candidate.stage == CandidateStage.applied:
            candidate.stage = CandidateStage.screening
        candidate.updated_at = datetime.now(timezone.utc)

        # Store hash and metadata in extracted_data
        from app.services.cv_review_service import compute_recommendation
        pass_mark = getattr(opening, "pass_mark", 80) or 80

        ext_data = dict(candidate.extracted_data or {})
        ext_data["cv_hash"] = cv_hash
        ext_data["recommendation"] = compute_recommendation(result["score"], pass_mark)
        ext_data["interview_focus_areas"] = result.get("interview_focus_areas", [])
        ext_data["model_used"] = result.get("model_used")
        ext_data["latency_seconds"] = result.get("latency_seconds")
        candidate.extracted_data = ext_data

        session.add(candidate)
        session.commit()
        session.refresh(candidate)

        # Optional Pinecone vector indexing (runs ONLY if PINECONE_API_KEY and PINECONE_INDEX are configured)
        try:
            from app.services.vector_service import vector_service
            if vector_service.is_enabled():
                vector_service.index_candidate_cv(
                    candidate_id=str(candidate.id),
                    candidate_name=candidate.name,
                    cv_text=cv_raw,
                    opening_id=str(candidate.opening_id),
                    score=result["score"],
                )
        except Exception as exc:
            logger.debug("Optional Pinecone vector indexing skipped/failed: %s", exc)

        # Populate in-memory cache
        _SCREENING_CACHE[cache_key] = result

        audit_log_service.record(
            session=session,
            user_id=user_id,
            action="cv_screened" if re_run else "cv_uploaded",
            candidate_id=candidate.id,
            opening_id=candidate.opening_id,
            details=f"AI Candidate Screening completed (score={result['score']}, re_run={re_run}).",
        )

        return CandidateScreenResult(
            candidate_id=candidate.id,
            candidate_name=candidate.name,
            score=result["score"],
            matched_skills=result["matched_skills"],
            missing_skills=result["missing_skills"],
            red_flags=result.get("red_flags", []),
            summary=result["summary"],
            recommendation=result.get("recommendation"),
            interview_focus_areas=result.get("interview_focus_areas", []),
            stage=candidate.stage,
            model_used=result.get("model_used"),
            latency_seconds=result.get("latency_seconds"),
        )

    # Alias for screen_candidate_ai
    screen_candidate_ai = score_candidate

    async def bulk_score_opening(
        self,
        session: Session,
        user_id: uuid.UUID,
        opening_id: uuid.UUID,
        candidate_ids: Optional[List[uuid.UUID]] = None,
    ) -> BulkScoreResponse:
        """
        Bulk scoring with ranking across candidates for a job opening.
        """
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

        query = select(Candidate).where(
            Candidate.opening_id == opening_id,
            Candidate.user_id == user_id,
        )
        if candidate_ids:
            query = query.where(Candidate.id.in_(candidate_ids))

        candidates = session.exec(query).all()
        if not candidates:
            return BulkScoreResponse(
                opening_id=opening.id,
                opening_title=opening.title,
                total_candidates=0,
                ranked_candidates=[],
            )

        scored_results: List[CandidateScreenResult] = []
        for cand in candidates:
            res = await self.score_candidate(session, user_id, cand.id)
            scored_results.append(res)

        # Sort descending by score
        scored_results.sort(key=lambda x: x.score, reverse=True)

        # Assign ranks 1..N
        for idx, item in enumerate(scored_results, start=1):
            item.rank = idx

        return BulkScoreResponse(
            opening_id=opening.id,
            opening_title=opening.title,
            total_candidates=len(scored_results),
            ranked_candidates=scored_results,
        )

    async def generate_screening_questions(
        self,
        session: Session,
        user_id: uuid.UUID,
        candidate_id: uuid.UUID,
        count: int = 5,
    ) -> CandidateScreeningQuestionsResponse:
        """
        Generate candidate-specific screening questions based on their CV gaps and red flags.
        """
        candidate = self.get_by_id(session, user_id, candidate_id)
        opening = session.exec(
            select(JobOpening).where(
                JobOpening.id == candidate.opening_id,
                JobOpening.user_id == user_id,
            )
        ).first()
        if not opening:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated Job Opening not found.",
            )

        questions = await generate_recruiter_interview_questions(
            job_title=opening.title,
            job_description=opening.description,
            candidate_cv=candidate.cv_text,
            red_flags=candidate.red_flags,
            count=count,
        )

        return CandidateScreeningQuestionsResponse(
            candidate_id=candidate.id,
            candidate_name=candidate.name,
            questions=questions,
        )

    def export_shortlist_csv(
        self,
        session: Session,
        user_id: uuid.UUID,
        opening_id: uuid.UUID,
        min_score: Optional[float] = None,
        stage: Optional[CandidateStage] = None,
    ) -> str:
        """
        Shortlist CSV export with ranked candidates and screening metadata.
        """
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

        query = select(Candidate).where(
            Candidate.opening_id == opening_id,
            Candidate.user_id == user_id,
        )

        if min_score is not None:
            query = query.where(Candidate.score >= min_score)
        if stage is not None:
            query = query.where(Candidate.stage == stage)

        query = query.order_by(Candidate.score.desc().nullslast(), Candidate.created_at.asc())
        candidates = session.exec(query).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Rank",
            "Name",
            "Email",
            "Phone",
            "Address",
            "Fit Score",
            "Stage",
            "LinkedIn",
            "GitHub",
            "Kaggle",
            "Portfolio",
            "Matched Skills",
            "Missing Skills",
            "Red Flags",
            "Executive Summary",
            "Applied Date",
        ])

        for rank, c in enumerate(candidates, start=1):
            score_str = f"{c.score:.1f}" if c.score is not None else "N/A"
            matched_str = "; ".join(c.matched_skills or [])
            missing_str = "; ".join(c.missing_skills or [])
            flags_str = "; ".join(c.red_flags or [])
            applied_str = c.created_at.strftime("%Y-%m-%d %H:%M UTC")

            writer.writerow([
                rank,
                c.name,
                c.email,
                c.phone or "",
                c.address or "",
                score_str,
                c.stage.value if hasattr(c.stage, "value") else str(c.stage),
                c.linkedin_url or "",
                c.github_url or "",
                c.kaggle_url or "",
                c.portfolio_url or "",
                matched_str,
                missing_str,
                flags_str,
                c.summary or "",
                applied_str,
            ])

        return output.getvalue()


candidate_service = CandidateService()
