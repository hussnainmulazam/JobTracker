"""Google Integration Router — status, disconnection, Gmail background sync, email conversations & threads, and sending emails."""
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlmodel import Session, col, select

logger = logging.getLogger(__name__)

from app.core.dependencies import CurrentUser
from app.db import SessionDep
from app.models.google_account import GoogleAccount
from app.models.job_opening import JobOpening
from app.models.candidate import Candidate, CandidateStage
from app.models.message import Message, MessageDirection, MessageStatus, MessageType
from app.schemas.google import (
    GmailSyncResponse,
    GoogleAccountStatusResponse,
    GoogleAccountUpdateRequest,
    GooglePreviewEmailRequest,
    GooglePreviewEmailResponse,
    GoogleSendEmailRequest,
    GoogleSendEmailResponse,
    EmailConversationSummary,
    EmailConversationsResponse,
    EmailMessageItem,
    EmailMessageAttachment,
    EmailThreadResponse,
    EmailReplyRequest,
    EmailAIDraftRequest,
    EmailAIDraftResponse,
)
from app.services.google_service import GoogleService

router = APIRouter(tags=["Google Integration"])


@router.get(
    "/integrations/google/status",
    response_model=GoogleAccountStatusResponse,
    summary="Get Google connection and Gmail sync status",
)
def get_google_status(
    current_user: CurrentUser,
    session: SessionDep,
) -> GoogleAccountStatusResponse:
    """Returns whether Google OAuth is connected, granted scopes, reconnect banner info, and last sync status."""
    service = GoogleService(session)
    return service.get_status(current_user.id)


@router.post(
    "/integrations/google/disconnect",
    summary="Disconnect Google account and revoke tokens",
)
def disconnect_google(
    current_user: CurrentUser,
    session: SessionDep,
):
    """Disconnects linked Google account, revokes OAuth tokens, and clears credentials."""
    service = GoogleService(session)
    service.disconnect(current_user.id)
    return {"detail": "Google account disconnected successfully."}


@router.post(
    "/integrations/google/sync",
    response_model=GmailSyncResponse,
    summary="Trigger on-demand incremental Gmail resume sync",
)
def sync_gmail(
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    session: SessionDep,
    query: str = Query(default=None, description="Optional custom Gmail search query"),
    label: str = Query(default=None, description="Optional Gmail label ID (INBOX, STARRED, etc.)"),
) -> GmailSyncResponse:
    """
    Executes incremental Gmail resume sync:
    - Downloads PDF/DOCX attachments
    - Deterministically parses name, email, contact details
    - Deduplicates against existing candidates per opening
    - Ingests new candidates into the pipeline
    - Auto-screens CVs with fit scores and sends auto-acknowledgement emails
    """
    service = GoogleService(session)
    try:
        return service.sync_gmail(
            user_id=current_user.id,
            query=query,
            label=label,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.patch(
    "/integrations/google/settings",
    response_model=GoogleAccountStatusResponse,
    summary="Update Gmail sync query, label, and default opening assignment",
)
def update_sync_settings(
    payload: GoogleAccountUpdateRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> GoogleAccountStatusResponse:
    """Updates background sync query, label filter, or target default opening for incoming CVs."""
    account = session.exec(
        select(GoogleAccount).where(GoogleAccount.user_id == current_user.id)
    ).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No connected Google account found for this recruiter.",
        )

    if payload.default_opening_id is not None:
        if payload.default_opening_id:
            opening = session.exec(
                select(JobOpening).where(
                    JobOpening.id == payload.default_opening_id,
                    JobOpening.user_id == current_user.id,
                )
            ).first()
            if not opening:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"JobOpening '{payload.default_opening_id}' not found.",
                )
            account.default_opening_id = payload.default_opening_id
        else:
            account.default_opening_id = None

    if payload.sync_query is not None:
        account.sync_query = payload.sync_query
    if payload.sync_label is not None:
        account.sync_label = payload.sync_label
    if payload.auto_reply_enabled is not None:
        account.auto_reply_enabled = payload.auto_reply_enabled

    session.add(account)
    session.commit()
    session.refresh(account)

    service = GoogleService(session)
    return service.get_status(current_user.id)


@router.post(
    "/integrations/google/preview-email",
    response_model=GooglePreviewEmailResponse,
    summary="Preview candidate email with resolved template variables",
)
def preview_email(
    payload: GooglePreviewEmailRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> GooglePreviewEmailResponse:
    """Pre-renders an email template with candidate and job requisition variables."""
    service = GoogleService(session)
    try:
        return service.preview_email(current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/integrations/google/send-email",
    response_model=GoogleSendEmailResponse,
    summary="Send candidate email via Gmail API (gmail.send) from recruiter's account",
)
def send_email(
    payload: GoogleSendEmailRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> GoogleSendEmailResponse:
    """
    Sends email to candidate using the connected recruiter's Gmail account (gmail.send).
    Stores outbound record in messages table and records in audit trail.
    """
    service = GoogleService(session)
    try:
        return service.send_email(current_user.id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/integrations/google/conversations",
    response_model=EmailConversationsResponse,
    summary="List recruiting email conversations across candidates",
)
@router.get(
    "/whatsapp/conversations",
    response_model=EmailConversationsResponse,
    include_in_schema=False,
)
def list_conversations(
    current_user: CurrentUser,
    session: SessionDep,
    filter_status: Optional[str] = Query(default="all"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=100),
) -> EmailConversationsResponse:
    """
    Lists email conversations grouped by candidate with unread counts and channel filtering.
    Optimized:
    - No synchronous Gmail network sync (served purely from local DB).
    - Single batch SQL query replaces N+1 candidate message queries.
    - Slices to paginated window (skip/limit).
    - Logs execution latency metrics.
    """
    t_start = time.perf_counter()

    # 1. Fetch candidate list
    candidates = session.exec(
        select(Candidate)
        .where(Candidate.user_id == current_user.id)
        .order_by(Candidate.updated_at.desc())
    ).all()

    openings_map = {
        op.id: op.title
        for op in session.exec(select(JobOpening).where(JobOpening.user_id == current_user.id)).all()
    }

    # 2. Batch fetch messages in ONE single query (no N+1 loop)
    cand_ids = [c.id for c in candidates]
    msgs_by_candidate: dict[uuid.UUID, list[Message]] = {}
    if cand_ids:
        all_msgs = session.exec(
            select(Message)
            .where(Message.user_id == current_user.id, col(Message.candidate_id).in_(cand_ids))
            .order_by(Message.created_at.desc())
        ).all()
        for m in all_msgs:
            msgs_by_candidate.setdefault(m.candidate_id, []).append(m)

    t_db = time.perf_counter() - t_start

    conversations = []
    awaiting_count = 0
    unread_total = 0

    for cand in candidates:
        msgs = msgs_by_candidate.get(cand.id, [])

        last_msg = msgs[0] if msgs else None
        dir_val = (last_msg.direction.value if hasattr(last_msg.direction, "value") else str(last_msg.direction)).lower() if last_msg else "inbound"
        is_awaiting = last_msg is not None and dir_val == "inbound"
        cand_stage_str = cand.stage.value if hasattr(cand.stage, "value") else str(cand.stage)
        has_unread = is_awaiting or (cand_stage_str == "applied" and not msgs)

        if is_awaiting:
            awaiting_count += 1
        if has_unread:
            unread_total += 1

        last_type = "whatsapp" if (last_msg and (last_msg.message_type == MessageType.text or last_msg.message_type == MessageType.template or "whatsapp" in str(last_msg.message_type).lower())) else "email"
        has_att = bool(cand.cv_file_url) or any(bool((m.template_variables or {}).get("attachments")) for m in msgs)

        has_whatsapp = (last_type == "whatsapp") or any(
            (m.message_type == MessageType.text or m.message_type == MessageType.template or "whatsapp" in str(m.message_type).lower())
            for m in msgs
        ) or bool(cand.phone)
        has_email = (last_type == "email") or any(
            (m.message_type == MessageType.email or "email" in str(m.message_type).lower())
            for m in msgs
        ) or bool(cand.email)

        # Apply filter_status: all, unread, awaiting_reply, email, whatsapp
        if filter_status == "unread" and not has_unread:
            continue
        elif filter_status == "awaiting_reply" and not is_awaiting:
            continue
        elif filter_status == "email" and not has_email:
            continue
        elif filter_status == "whatsapp" and not has_whatsapp:
            continue

        subj = None
        if last_msg:
            subj = (last_msg.template_variables or {}).get("subject") or last_msg.template_name or "Communication"
        else:
            subj = f"Application for {openings_map.get(cand.opening_id, 'Open Role')}"

        body_preview = ""
        if last_msg:
            body_preview = last_msg.body[:140] if last_msg.body else ""
        else:
            body_preview = f"Candidate submitted application for {openings_map.get(cand.opening_id, 'Open Role')}."

        conv = EmailConversationSummary(
            candidate_id=cand.id,
            candidate_name=cand.name,
            candidate_email=cand.email,
            candidate_phone=cand.phone,
            candidate_stage=cand_stage_str,
            opening_title=openings_map.get(cand.opening_id, "General Applications"),
            last_message_body=body_preview,
            last_message_subject=subj,
            last_message_direction=dir_val,
            last_message_type=last_type,
            last_message_at=last_msg.created_at if last_msg else cand.created_at,
            unread=has_unread,
            unread_count=1 if is_awaiting else 0,
            has_attachments=has_att,
        )
        conversations.append(conv)

    # Sort grouped candidate threads newest first
    conversations.sort(
        key=lambda c: c.last_message_at or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    total_count = len(conversations)
    paginated_convs = conversations[skip : skip + limit]

    t_total = time.perf_counter() - t_start
    logger.info(
        "[TIMING] list_conversations: total_ms=%.2f db_ms=%.2f total_candidates=%d paginated=%d",
        t_total * 1000,
        t_db * 1000,
        total_count,
        len(paginated_convs),
    )

    return EmailConversationsResponse(
        conversations=paginated_convs,
        total_conversations=total_count,
        awaiting_reply_count=awaiting_count,
        unread_count=unread_total,
    )


@router.get(
    "/integrations/google/threads/{candidate_id}",
    response_model=EmailThreadResponse,
    summary="Get candidate email thread history",
)
def get_thread(
    candidate_id: uuid.UUID,
    current_user: CurrentUser,
    session: SessionDep,
) -> EmailThreadResponse:
    """Returns candidate details and full email communication thread history."""
    t0 = time.perf_counter()
    cand = session.exec(
        select(Candidate).where(Candidate.id == candidate_id, Candidate.user_id == current_user.id)
    ).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    opening = session.exec(
        select(JobOpening).where(JobOpening.id == cand.opening_id)
    ).first()

    messages = session.exec(
        select(Message)
        .where(Message.candidate_id == candidate_id, Message.user_id == current_user.id)
        .order_by(Message.created_at.asc())
    ).all()

    msg_items: List[EmailMessageItem] = []

    # If candidate has CV attachment or text, and no inbound messages exist yet, synthesize the initial application message
    has_inbound = any(m.direction == MessageDirection.inbound for m in messages)
    if not has_inbound and (cand.cv_file_url or cand.cv_text):
        init_atts: List[EmailMessageAttachment] = []
        if cand.cv_file_url:
            filename = cand.cv_file_url.split("/")[-1].split("?")[0] or f"{cand.name.replace(' ', '_')}_Resume.pdf"
            init_atts.append(
                EmailMessageAttachment(
                    filename=filename,
                    url=cand.cv_file_url,
                    mime_type="application/pdf",
                )
            )
        msg_items.append(
            EmailMessageItem(
                id=cand.id,
                candidate_id=cand.id,
                direction="inbound",
                message_type="email",
                subject=f"Application for {opening.title if opening else 'Open Position'}",
                body=f"Hello,\n\nPlease find attached my resume for the {opening.title if opening else 'open'} role.\n\nLooking forward to connecting with your recruiting team.\n\nBest regards,\n{cand.name}",
                status="delivered",
                created_at=cand.created_at,
                sent_at=cand.created_at,
                attachments=init_atts,
            )
        )

    for m in messages:
        m_type = "whatsapp" if (m.message_type == MessageType.text or m.message_type == MessageType.template or "whatsapp" in str(m.message_type).lower()) else "email"
        subj = (m.template_variables or {}).get("subject") or m.template_name or ("Email Message" if m_type == "email" else "WhatsApp Message")
        th_id = (m.template_variables or {}).get("thread_id") or (m.template_variables or {}).get("google_message_id")
        raw_atts = (m.template_variables or {}).get("attachments") or []
        parsed_atts = []
        for a in raw_atts:
            if isinstance(a, dict) and "url" in a:
                parsed_atts.append(EmailMessageAttachment(**a))

        msg_items.append(
            EmailMessageItem(
                id=m.id,
                candidate_id=m.candidate_id,
                direction=m.direction.value if hasattr(m.direction, "value") else str(m.direction),
                message_type=m_type,
                subject=subj,
                body=m.body,
                status=m.status.value if hasattr(m.status, "value") else str(m.status),
                sent_at=m.sent_at,
                created_at=m.created_at,
                thread_id=th_id,
                attachments=parsed_atts,
            )
        )

    t_total = time.perf_counter() - t0
    logger.info("[TIMING] get_thread: candidate_id=%s total_ms=%.2f msg_count=%d", candidate_id, t_total * 1000, len(msg_items))

    return EmailThreadResponse(
        candidate_id=cand.id,
        candidate_name=cand.name,
        candidate_email=cand.email,
        candidate_stage=cand.stage.value if hasattr(cand.stage, "value") else str(cand.stage),
        opening_title=opening.title if opening else "Position",
        messages=msg_items,
    )


@router.post(
    "/integrations/google/reply",
    response_model=GoogleSendEmailResponse,
    summary="Send reply email in candidate thread",
)
def send_reply(
    payload: EmailReplyRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> GoogleSendEmailResponse:
    """Dispatches a direct email reply to candidate via Gmail API within the same thread."""
    service = GoogleService(session)
    cand = session.exec(
        select(Candidate).where(Candidate.id == payload.candidate_id, Candidate.user_id == current_user.id)
    ).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    # Check for existing thread ID to keep reply in the same Gmail thread
    last_msg = session.exec(
        select(Message)
        .where(Message.candidate_id == payload.candidate_id, Message.user_id == current_user.id)
        .order_by(Message.created_at.desc())
    ).first()
    thread_id = None
    if last_msg and last_msg.template_variables:
        thread_id = last_msg.template_variables.get("thread_id") or last_msg.template_variables.get("google_message_id")

    subj = payload.subject or "Next steps regarding your application"
    send_req = GoogleSendEmailRequest(
        candidate_id=payload.candidate_id,
        subject=subj,
        body=payload.message,
        template_name="candidate_email_reply",
        thread_id=thread_id,
    )
    return service.send_email(current_user.id, send_req)


@router.post(
    "/integrations/google/ai-draft-reply",
    response_model=EmailAIDraftResponse,
    summary="AI draft response to candidate email",
)
async def ai_draft_reply(
    payload: EmailAIDraftRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> EmailAIDraftResponse:
    """Generates an AI personalized email response using candidate and job context."""
    cand = session.exec(
        select(Candidate).where(Candidate.id == payload.candidate_id, Candidate.user_id == current_user.id)
    ).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    opening = session.exec(
        select(JobOpening).where(JobOpening.id == cand.opening_id)
    ).first()
    job_title = opening.title if opening else "Position"
    first_name = cand.name.split()[0] if cand.name else "there"

    sys_prompt = (
        "You are an empathetic, professional recruiter writing directly to a job applicant. "
        "Your tone is warm, natural, conversational, and direct. "
        "NEVER use generic corporate fluff, robotic cliches (such as 'I hope this email finds you well', 'We are pleased to inform you', 'Delving into', 'Tapestry'), or bracketed placeholders. "
        "Keep it concise, courteous, and under 90 words."
    )
    user_prompt = (
        f"Candidate Name: {cand.name}\n"
        f"Role: {job_title}\n"
        f"Key Skills: {', '.join((cand.matched_skills or [])[:4])}\n"
        f"Instructions: {payload.instructions or 'Follow up warmly about moving to the next conversation and ask for their availability for a brief call this week.'}\n\n"
        f"Write a warm, human, short email reply addressing {first_name}."
    )

    drafted_text = ""
    try:
        from app.services.ai_router import ai_router
        drafted_text, _, _ = await ai_router.complete_with_chain(
            task_name="drafts",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )
    except Exception:
        drafted_text = (
            f"Hi {first_name},\n\n"
            f"Thanks for applying for the {job_title} role. We reviewed your background and would love to chat further. "
            f"Could you let me know what times work best for a quick 20-minute introductory call this week?\n\n"
            f"Looking forward to speaking with you!\n\n"
            f"Best regards,\nTalent Team"
        )

    return EmailAIDraftResponse(
        candidate_id=cand.id,
        drafted_subject=f"Re: Opportunities for {job_title}",
        drafted_message=drafted_text.strip(),
    )
