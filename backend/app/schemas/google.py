"""Google integration schemas — validation and serialization for Google OAuth2, Gmail sync, and email sending."""
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GoogleAuthUrlResponse(BaseModel):
    auth_url: str = Field(..., description="Google OAuth2 consent screen URL")
    state: str = Field(..., description="Secure CSRF state token encoding user session")


class EmailSyncItemResult(BaseModel):
    message_id: str
    sender: Optional[str] = None
    subject: Optional[str] = None
    status: str = Field(..., description="Outcome: created, duplicate, or failed")
    candidate_id: Optional[str] = None
    candidate_name: Optional[str] = None
    opening_title: Optional[str] = None
    reason: Optional[str] = None


class GoogleAccountStatusResponse(BaseModel):
    is_connected: bool = Field(..., description="Whether recruiter has linked their Google account")
    email: Optional[str] = Field(default=None, description="Linked Google account email")
    scopes: List[str] = Field(default_factory=list, description="OAuth scopes granted by recruiter")
    missing_scopes: List[str] = Field(default_factory=list, description="Required scopes that have not been granted yet")
    granted_services: Dict[str, bool] = Field(
        default_factory=dict,
        description="Map of workspace services (Gmail, Calendar, Meet, Sheets, Docs, Drive) to granted status",
    )
    reconnect_needed: bool = Field(default=False, description="Whether re-authentication is required due to missing scopes or token revocation")
    reconnect_reason: Optional[str] = Field(default=None, description="Detailed explanation for why reconnection is needed")
    last_synced_at: Optional[datetime] = Field(default=None, description="Timestamp of last Gmail sync")
    last_sync_status: str = Field(default="never", description="Status of last sync: never, success, partial, failed, token_revoked")
    sync_query: str = Field(
        default="has:attachment (filename:pdf OR filename:docx) newer_than:30d",
        description="Gmail search filter query used for syncing candidate resumes",
    )
    sync_label: str = Field(default="INBOX", description="Gmail label to sync from")
    auto_reply_enabled: bool = Field(default=True, description="Whether to automatically send CV received email on intake")
    default_opening_id: Optional[uuid.UUID] = Field(default=None, description="Default job opening for incoming resumes without subject match")
    default_opening_title: Optional[str] = Field(default=None, description="Title of default job opening")
    total_emails_synced: int = Field(default=0, description="Total resume emails processed")
    synced_from_gmail_count: int = Field(default=0, description="Total candidates created from Gmail sync")
    recent_sync_results: List[EmailSyncItemResult] = Field(default_factory=list, description="Recent sync outcomes per email")


class GoogleAccountUpdateRequest(BaseModel):
    sync_query: Optional[str] = Field(default=None, min_length=1, max_length=500)
    sync_label: Optional[str] = Field(default=None, min_length=1, max_length=100)
    auto_reply_enabled: Optional[bool] = Field(default=None, description="Toggle auto-reply confirmation email")
    default_opening_id: Optional[uuid.UUID] = Field(default=None, description="Set default job opening for Gmail resumes")


class GmailSyncResponse(BaseModel):
    status: str = Field(..., description="Sync outcome: success, partial, or failed")
    messages_found: int = Field(..., description="Total candidate messages found matching query")
    messages_processed: int = Field(..., description="New candidate messages processed")
    attachments_saved: int = Field(..., description="PDF/DOCX resumes extracted and stored")
    candidates_created: int = Field(..., description="Candidate profiles created in database")
    synced_from_gmail_count: int = Field(default=0, description="Total candidates created from Gmail sync")
    results: List[EmailSyncItemResult] = Field(default_factory=list, description="Per-email sync outcome details")
    errors: List[str] = Field(default_factory=list, description="Any warnings, failures, or rate limit notices encountered")
    last_synced_at: datetime = Field(..., description="Current sync timestamp")


class EmailSyncedRead(BaseModel):
    id: uuid.UUID
    message_id: str
    thread_id: Optional[str] = None
    sender: Optional[str] = None
    subject: Optional[str] = None
    snippet: Optional[str] = None
    attachment_names: List[str] = Field(default_factory=list)
    attachment_urls: List[str] = Field(default_factory=list)
    synced_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GooglePreviewEmailRequest(BaseModel):
    candidate_id: uuid.UUID = Field(..., description="Candidate recipient ID")
    template_name: str = Field(default="interview_invitation", description="Template key or 'custom'")
    custom_subject: Optional[str] = Field(default=None, description="Custom subject when template is custom or override")
    custom_body: Optional[str] = Field(default=None, description="Custom body when template is custom or override")
    slot_link: Optional[str] = Field(default=None, description="Candidate self-scheduling slot link")
    company_name: Optional[str] = Field(default=None, description="Company name override")


class GooglePreviewEmailResponse(BaseModel):
    candidate_id: uuid.UUID
    candidate_name: str
    candidate_email: str
    recipient_email: Optional[str] = None
    subject: str
    body: str
    variables: Dict[str, str] = Field(default_factory=dict)


class GoogleSendEmailRequest(BaseModel):
    candidate_id: uuid.UUID = Field(..., description="Candidate recipient ID")
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    html_body: Optional[str] = Field(default=None, description="Optional HTML version of the message for multipart/alternative")
    template_name: Optional[str] = Field(default="custom", description="Template name used, if any")
    thread_id: Optional[str] = Field(default=None, description="Gmail thread ID to reply within the same thread")
    force_resend: bool = Field(default=False, description="Bypass idempotency check if recruiter explicitly wants to re-send")


class GoogleSendEmailResponse(BaseModel):
    message_id: uuid.UUID
    candidate_id: uuid.UUID
    recipient_email: str
    subject: str
    status: str
    sent_at: datetime
    google_message_id: Optional[str] = None


class EmailMessageAttachment(BaseModel):
    filename: str
    url: str
    size: Optional[str] = None
    mime_type: Optional[str] = None


class EmailConversationSummary(BaseModel):
    candidate_id: uuid.UUID
    candidate_name: str
    candidate_email: str
    candidate_phone: Optional[str] = None
    candidate_stage: str
    opening_title: Optional[str] = None
    last_message_body: Optional[str] = None
    last_message_subject: Optional[str] = None
    last_message_direction: Optional[str] = None
    last_message_type: str = "email"
    last_message_at: Optional[datetime] = None
    unread: bool = False
    unread_count: int = 0
    has_attachments: bool = False


class EmailConversationsResponse(BaseModel):
    conversations: List[EmailConversationSummary] = Field(default_factory=list)
    total_conversations: int = 0
    awaiting_reply_count: int = 0
    unread_count: int = 0


class EmailMessageItem(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    direction: str
    message_type: str = "email"
    subject: Optional[str] = None
    body: str
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime
    thread_id: Optional[str] = None
    attachments: List[EmailMessageAttachment] = Field(default_factory=list)


class EmailThreadResponse(BaseModel):
    candidate_id: uuid.UUID
    candidate_name: str
    candidate_email: str
    candidate_stage: str
    opening_title: Optional[str] = None
    messages: List[EmailMessageItem] = Field(default_factory=list)


class EmailReplyRequest(BaseModel):
    candidate_id: uuid.UUID
    message: str = Field(..., min_length=1)
    subject: Optional[str] = None


class EmailAIDraftRequest(BaseModel):
    candidate_id: uuid.UUID
    instructions: Optional[str] = None


class EmailAIDraftResponse(BaseModel):
    candidate_id: uuid.UUID
    drafted_subject: str
    drafted_message: str
