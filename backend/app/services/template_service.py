"""
backend/app/services/template_service.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Service for database-backed recruiting email templates (Single Source of Truth).
Rules:
1. Templates come ONLY from the database table 'recruiting_templates'.
2. Missing default templates are seeded once per HR account and never overwrite HR edits.
3. The agent workflow and every email/WhatsApp sender load templates by stage key from this table only. No hardcoded email text anywhere in code.
4. If a template is missing or disabled: pause that step with "Template missing: <name>" and a link to Settings. Never send a fallback.
5. At send time only fill variables: {candidate_name} {role} {company} {hr_name} {interview_date} {interview_time} {meet_link} {schedule_link} {job_details}. Never call the LLM to write email text at send time. A missing variable blocks sending and flags HR.
6. Cache templates with a short TTL and clear the cache on every save, regenerate, disable or duplicate.
"""
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Set
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.models.recruiting_template import RecruitingTemplate
from app.services.ai_router import ai_router
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

# Cache TTL for templates: 60s (short TTL)
TEMPLATE_CACHE_TTL = 60


def clear_user_template_cache(user_id: Optional[uuid.UUID] = None) -> None:
    """Invalidates template cache for a specific user or all users."""
    if user_id:
        cache_service.delete(f"templates:user:{user_id}")
    else:
        cache_service.delete_prefix("templates:user:")


class MissingTemplateVariablesError(Exception):
    """Raised when an email cannot be sent due to missing required template variables."""
    pass


class TemplateMissingOrDisabledError(Exception):
    """Raised when a required lifecycle template is missing or disabled in the DB."""
    def __init__(self, stage_name: str, settings_link: str = "/settings?tab=templates"):
        self.stage_name = stage_name
        self.settings_link = settings_link
        super().__init__(f"Template missing: {stage_name}. Configure at {settings_link}")


class TemplateNotFoundError(TemplateMissingOrDisabledError):
    """Alias for backwards compatibility."""
    pass


TEMPLATE_ALIASES: Dict[str, str] = {
    "interview_invitation": "initial_interview",
    "interview_invite": "initial_interview",
    "application_rejected": "rejection",
    "interview_rejected": "rejection",
    "application_approved": "cv_passed",
    "initial_screen": "initial_interview",
    "behavioral": "behavioral_interview",
    "final_round": "final_interview",
    "application_on_hold": "rejection",
    "interview_reminder_24h": "interview_reminder",
    "interview_reminder_1h": "interview_reminder",
    "hr_interviewer_reminder": "interview_reminder",
    "hr_interview_scheduled": "initial_interview",
    "interview_confirmed": "initial_interview",
    "interview_rescheduled": "initial_interview",
    "interview_cancellation": "rejection",
    "interview_cancelled": "rejection",
    "interview_reschedule": "initial_interview",
    "interview_confirmation": "initial_interview",
    "application_approved_interview_invitation": "cv_passed",
}

TEMPLATE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "cv_received": {
        "name": "CV Received",
        "description": "Sent when an applicant's CV is first received to confirm intake.",
        "variables": ["candidate_name", "role", "company", "hr_name"],
    },
    "cv_passed": {
        "name": "CV Passed",
        "description": "Sent when candidate's CV is approved / shortlisted.",
        "variables": ["candidate_name", "role", "company", "hr_name", "schedule_link"],
    },
    "job_details": {
        "name": "Job Details",
        "description": "Shares the role responsibilities, tech stack, and team culture.",
        "variables": ["candidate_name", "role", "company", "hr_name", "job_details", "schedule_link"],
    },
    "initial_interview": {
        "name": "Initial Interview",
        "description": "Invites candidate to an initial 30-min screening call.",
        "variables": ["candidate_name", "role", "company", "hr_name", "schedule_link"],
    },
    "initial_passed": {
        "name": "Initial Passed",
        "description": "Congratulates candidate on passing the initial screening round.",
        "variables": ["candidate_name", "role", "company", "hr_name", "schedule_link"],
    },
    "behavioral_interview": {
        "name": "Behavioral Interview",
        "description": "Invites candidate to the behavioral and cultural alignment round.",
        "variables": ["candidate_name", "role", "company", "hr_name", "interview_date", "interview_time", "meet_link", "schedule_link"],
    },
    "behavioral_passed": {
        "name": "Behavioral Passed",
        "description": "Notifies candidate they passed the behavioral evaluation.",
        "variables": ["candidate_name", "role", "company", "hr_name", "schedule_link"],
    },
    "final_interview": {
        "name": "Final Interview",
        "description": "Invites candidate to the final leadership interview.",
        "variables": ["candidate_name", "role", "company", "hr_name", "interview_date", "interview_time", "meet_link", "schedule_link"],
    },
    "offer_letter": {
        "name": "Offer Letter",
        "description": "Celebratory job offer extending employment details.",
        "variables": ["candidate_name", "role", "company", "hr_name"],
    },
    "rejection": {
        "name": "Rejection (per stage)",
        "description": "Short, kind, and appreciative rejection message.",
        "variables": ["candidate_name", "role", "company", "hr_name"],
    },
    "interview_reminder": {
        "name": "Interview Reminder",
        "description": "Friendly reminder 24h or 1h before a scheduled interview.",
        "variables": ["candidate_name", "role", "company", "hr_name", "interview_date", "interview_time", "meet_link"],
    },
}

SUPPORTED_VARIABLE_KEYS: Set[str] = {
    "candidate_name",
    "role",
    "company",
    "hr_name",
    "interview_date",
    "interview_time",
    "meet_link",
    "schedule_link",
    "job_details",
    "signature",
}


class TemplateItemSchema(BaseModel):
    name: Optional[str] = None
    subject: str = Field(..., min_length=2)
    body: str = Field(..., min_length=5)
    is_active: bool = True
    is_default: bool = True
    is_custom: bool = False


class TemplatesBatchSchema(BaseModel):
    templates: Dict[str, TemplateItemSchema]


def get_default_templates(
    hr_name: str = "Our Team",
    company_name: str = "Our Team",
    email_tone: str = "warm_professional",
) -> Dict[str, Dict[str, str]]:
    """
    Returns authentic, short, and warm human templates for all 11 stages.
    Never robotic; uses clean conversational recruiter language.
    Only used once to seed missing defaults in the DB.
    """
    is_casual = "casual" in (email_tone or "").lower()
    is_direct = "direct" in (email_tone or "").lower()
    is_formal = "formal" in (email_tone or "").lower()

    if is_casual:
        salutation = "Hey {candidate_name}!"
        signoff = f"Cheers,\n{hr_name}\n{{company}}"
    elif is_direct:
        salutation = "Hi {candidate_name},"
        signoff = f"Best,\n{hr_name}\n{{company}}"
    elif is_formal:
        salutation = "Dear {candidate_name},"
        signoff = f"Sincerely,\n{hr_name}\n{{company}}"
    else:
        salutation = "Hi {candidate_name},"
        signoff = f"Warm regards,\n{hr_name}\n{{company}}"

    return {
        "cv_received": {
            "name": "CV Received",
            "subject": "Got your application for {role} at {company}!",
            "body": (
                f"{salutation}\n\n"
                "Thank you for sharing your application with us! We have received your CV for the {role} position.\n\n"
                "Our team is reviewing your background and qualifications. We will get back to you as soon as we've reviewed your materials.\n\n"
                f"{signoff}"
            ),
        },
        "cv_passed": {
            "name": "CV Passed",
            "subject": "Great news regarding your application for {role} at {company}",
            "body": (
                f"{salutation}\n\n"
                "Your background caught our eye! Your skills and experience align closely with what we're building for {role} at {company}.\n\n"
                "We'd love to chat and get to know you better. Please pick a time that works best for you here:\n"
                "{schedule_link}\n\n"
                f"{signoff}"
            ),
        },
        "job_details": {
            "name": "Job Details",
            "subject": "More details about the {role} opening at {company}",
            "body": (
                f"{salutation}\n\n"
                "Here are a few more details on what the {role} role looks like day-to-day at {company}:\n\n"
                "{job_details}\n\n"
                "If this sounds exciting to you, schedule your introductory call here:\n"
                "{schedule_link}\n\n"
                f"{signoff}"
            ),
        },
        "initial_interview": {
            "name": "Initial Interview",
            "subject": "Let's connect: {role} at {company}",
            "body": (
                f"{salutation}\n\n"
                "We would love to invite you to an introductory 30-minute chat for the {role} opening. "
                "It's an informal conversation to learn about your goals and share more about the role.\n\n"
                "Choose a slot that suits your schedule here:\n"
                "{schedule_link}\n\n"
                f"{signoff}"
            ),
        },
        "initial_passed": {
            "name": "Initial Passed",
            "subject": "Great speaking with you! Next steps for {role} at {company}",
            "body": (
                f"{salutation}\n\n"
                "I really enjoyed our introductory conversation. The team was impressed by your experience and we are excited to move you forward to the next round!\n\n"
                "Please use this booking link to schedule your next session:\n"
                "{schedule_link}\n\n"
                f"{signoff}"
            ),
        },
        "behavioral_interview": {
            "name": "Behavioral Interview",
            "subject": "Team & Culture Fit Interview: {role} at {company}",
            "body": (
                f"{salutation}\n\n"
                "We'd love to invite you to our team alignment conversation for the {role} position. "
                "This session is a chance for you to meet the team, discuss how we work together, and ask any questions you have.\n\n"
                "If not already booked, pick a time here:\n"
                "{schedule_link}\n"
                "Meeting link: {meet_link}\n\n"
                f"{signoff}"
            ),
        },
        "behavioral_passed": {
            "name": "Behavioral Passed",
            "subject": "Wonderful feedback on your interview for {role} at {company}",
            "body": (
                f"{salutation}\n\n"
                "The team loved meeting with you! Your approach to collaboration and problem solving made a fantastic impression on everyone.\n\n"
                "We would love to move you to the final interview round. You can book your slot here:\n"
                "{schedule_link}\n\n"
                f"{signoff}"
            ),
        },
        "final_interview": {
            "name": "Final Interview",
            "subject": "Final Interview: {role} at {company}",
            "body": (
                f"{salutation}\n\n"
                "You have reached the final stage of our hiring process! This round will be a focused discussion with our leadership team.\n\n"
                "Interview timing: {interview_date} at {interview_time}\n"
                "Video room: {meet_link}\n\n"
                "We are excited for this conversation. Reach out if you need anything beforehand.\n\n"
                f"{signoff}"
            ),
        },
        "offer_letter": {
            "name": "Offer Letter",
            "subject": "Offer of Employment: Welcome to {company}!",
            "body": (
                f"{salutation}\n\n"
                "On behalf of everyone at {company}, I am thrilled to extend an offer for the {role} position! "
                "We were deeply inspired by your talent and believe you will do phenomenal work here.\n\n"
                "I will follow up shortly with your formal offer summary packet. In the meantime, huge congratulations—we can't wait to work together!\n\n"
                f"{signoff}"
            ),
        },
        "rejection": {
            "name": "Rejection (per stage)",
            "subject": "Update on your application for {role} at {company}",
            "body": (
                f"{salutation}\n\n"
                "Thank you sincerely for taking the time to speak with us about the {role} position at {company}. "
                "While our team was impressed by your background, we have chosen to move forward with another applicant whose experience is slightly closer to our current immediate priorities.\n\n"
                "We genuinely appreciate your time and enthusiasm. We'll keep your profile in our talent pool for future openings, and wish you all the best in your search.\n\n"
                f"{signoff}"
            ),
        },
        "interview_reminder": {
            "name": "Interview Reminder",
            "subject": "Reminder: Your upcoming interview with {company} for {role}",
            "body": (
                f"{salutation}\n\n"
                "Just a friendly reminder about our upcoming interview for the {role} role.\n\n"
                "Date & Time: {interview_date} at {interview_time}\n"
                "Google Meet Link: {meet_link}\n\n"
                "Looking forward to speaking with you soon! Let me know if you need to reschedule.\n\n"
                f"{signoff}"
            ),
        },
    }


def seed_missing_default_templates(session: Session, user_id: uuid.UUID) -> List[RecruitingTemplate]:
    """
    Requirement 2: Seed missing defaults ONCE per HR account.
    NEVER overwrite HR edits!
    If a template already exists for that user and stage_key, it is left untouched.
    If the user previously edited templates in OnboardingSetup.templates, those edits
    are preserved and transferred into the recruiting_templates table.
    """
    # 1. Fetch existing recruiting_templates rows for this user
    existing_templates = session.exec(
        select(RecruitingTemplate).where(RecruitingTemplate.user_id == user_id)
    ).all()
    existing_keys: Set[str] = {t.stage_key for t in existing_templates}

    # 2. Check if user has legacy/onboarding templates saved
    onboarding_templates: Dict[str, Any] = {}
    hr_name = "Recruiting Team"
    company_name = "Our Company"
    email_tone = "warm_professional"

    try:
        from app.models.onboarding import OnboardingSetup
        onboarding = session.exec(
            select(OnboardingSetup).where(OnboardingSetup.user_id == user_id)
        ).first()
        if onboarding:
            if onboarding.hr_name:
                hr_name = onboarding.hr_name
            if onboarding.company_name:
                company_name = onboarding.company_name
            if onboarding.email_tone:
                email_tone = onboarding.email_tone
            if onboarding.templates and isinstance(onboarding.templates, dict):
                onboarding_templates = onboarding.templates
    except Exception as exc:
        logger.debug("Could not read OnboardingSetup during template seeding: %s", exc)

    code_defaults = get_default_templates(hr_name=hr_name, company_name=company_name, email_tone=email_tone)

    inserted_count = 0
    now = datetime.now(timezone.utc)

    # 3. Seed only missing default stages
    for stage_key, cfg in TEMPLATE_CONFIGS.items():
        if stage_key in existing_keys:
            continue  # NEVER overwrite HR edits!

        # Check if user already edited this in OnboardingSetup
        user_saved = onboarding_templates.get(stage_key)
        if user_saved and isinstance(user_saved, dict) and user_saved.get("subject") and user_saved.get("body"):
            subject = user_saved.get("subject", "").strip()
            body = user_saved.get("body", "").strip()
            name = user_saved.get("name") or cfg.get("name", stage_key.replace("_", " ").title())
            is_active = user_saved.get("is_active", True)
        else:
            default_item = code_defaults.get(stage_key, {})
            subject = default_item.get("subject", f"Update regarding {{role}} at {{company}}")
            body = default_item.get("body", "Thank you for connecting with our team.")
            name = default_item.get("name", cfg.get("name", stage_key.replace("_", " ").title()))
            is_active = True

        new_tmpl = RecruitingTemplate(
            user_id=user_id,
            stage_key=stage_key,
            name=name,
            description=cfg.get("description", ""),
            subject=subject,
            body=body,
            is_active=is_active,
            is_default=True,
            is_custom=False,
            created_at=now,
            updated_at=now,
        )
        session.add(new_tmpl)
        inserted_count += 1

    if inserted_count > 0:
        session.commit()
        clear_user_template_cache(user_id)
        logger.info("Seeded %d missing default recruiting templates for user %s", inserted_count, user_id)

    return session.exec(
        select(RecruitingTemplate).where(RecruitingTemplate.user_id == user_id).order_by(RecruitingTemplate.created_at)
    ).all()


def get_user_templates_from_db(session: Session, user_id: uuid.UUID) -> List[RecruitingTemplate]:
    """
    Loads templates strictly from PostgreSQL recruiting_templates table.
    Caches with short TTL (60s).
    """
    cache_key = f"templates:user:{user_id}"
    cached = cache_service.get(cache_key)
    if cached is not None and isinstance(cached, list):
        return [RecruitingTemplate.model_validate(item) for item in cached]

    # Seed any missing defaults once (never overwriting user edits)
    templates = seed_missing_default_templates(session, user_id)

    # Cache as dictionaries for serialization safety
    serialized = [t.model_dump() for t in templates]
    cache_service.set(cache_key, serialized, ttl=TEMPLATE_CACHE_TTL)
    return templates


def get_template_for_stage(
    session: Session,
    user_id: uuid.UUID,
    stage_key: str,
) -> RecruitingTemplate:
    """
    Loads template strictly by stage key from the DB.
    Resolves aliases deterministically.
    If template is missing or disabled: raises TemplateMissingOrDisabledError.
    NEVER sends a fallback!
    """
    resolved_key = TEMPLATE_ALIASES.get(stage_key.lower().strip(), stage_key.lower().strip())
    templates = get_user_templates_from_db(session, user_id)

    # Filter matching candidates for this stage key
    matching = [
        t for t in templates
        if t.stage_key.lower() == resolved_key or t.stage_key.lower() == stage_key.lower()
    ]

    if not matching:
        # Check if there is an exact custom template matching stage_key
        matching = [t for t in templates if t.stage_key.lower() == stage_key.lower()]

    if not matching:
        cfg = TEMPLATE_CONFIGS.get(resolved_key) or TEMPLATE_CONFIGS.get(stage_key)
        name = cfg.get("name", stage_key.replace("_", " ").title()) if cfg else stage_key
        raise TemplateMissingOrDisabledError(stage_name=name)

    # Prefer is_default=True, then first active
    active_defaults = [t for t in matching if t.is_default and t.is_active]
    if active_defaults:
        return active_defaults[0]

    actives = [t for t in matching if t.is_active]
    if actives:
        return actives[0]

    # All matching templates are disabled!
    tmpl = matching[0]
    raise TemplateMissingOrDisabledError(stage_name=f"{tmpl.name} (disabled)")


def fill_template_variables(template_str: str, variables: Dict[str, Any]) -> str:
    """
    Pure deterministic variable substitution. Never calls AI.
    Handles both {variable} and {{variable}} patterns.
    """
    if not template_str:
        return ""
    result = template_str
    for k, v in variables.items():
        val = str(v) if v is not None else ""
        result = result.replace(f"{{{k}}}", val)
        result = result.replace(f"{{{{{k}}}}}", val)
    return result


def extract_template_variable_placeholders(text: str) -> Set[str]:
    """Finds all {var} and {{var}} placeholders within a template string."""
    if not text:
        return set()
    single_brace = set(re.findall(r"\{([a-zA-Z0-9_]+)\}", text))
    double_brace = set(re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", text))
    return single_brace.union(double_brace)


def render_user_template(
    session: Session,
    user_id: uuid.UUID,
    template_id: str,
    context: Dict[str, Any],
) -> Tuple[str, str, str, str]:
    """
    Requirement 3, 4 & 5:
    1. Loads template strictly from DB (single source of truth).
    2. If missing or disabled: raises TemplateMissingOrDisabledError. Never sends fallback.
    3. Strictly validates required variables: {candidate_name} {role} {company} {hr_name}
       {interview_date} {interview_time} {meet_link} {schedule_link} {job_details}.
       If any variable used in template is missing, blocks sending and flags HR.
    4. Never calls the LLM at send time — pure deterministic variable substitution.
    Returns: (subject, html_body, text_body, preheader)
    """
    tmpl = get_template_for_stage(session, user_id, template_id)

    raw_subject = tmpl.subject or ""
    raw_body = tmpl.body or ""

    # Normalize variable aliases for deterministic fill
    normalized_ctx: Dict[str, Any] = {k: v for k, v in context.items()}
    if "job_title" in normalized_ctx and "role" not in normalized_ctx:
        normalized_ctx["role"] = normalized_ctx["job_title"]
    if "role" in normalized_ctx and "job_title" not in normalized_ctx:
        normalized_ctx["job_title"] = normalized_ctx["role"]
    if "company_name" in normalized_ctx and "company" not in normalized_ctx:
        normalized_ctx["company"] = normalized_ctx["company_name"]
    if "company" in normalized_ctx and "company_name" not in normalized_ctx:
        normalized_ctx["company_name"] = normalized_ctx["company"]
    if "meeting_link" in normalized_ctx and "meet_link" not in normalized_ctx:
        normalized_ctx["meet_link"] = normalized_ctx["meeting_link"]
    if "meet_link" in normalized_ctx and "meeting_link" not in normalized_ctx:
        normalized_ctx["meeting_link"] = normalized_ctx["meet_link"]
    if "booking_link" in normalized_ctx and "schedule_link" not in normalized_ctx:
        normalized_ctx["schedule_link"] = normalized_ctx["booking_link"]
    if "slot_link" in normalized_ctx and "schedule_link" not in normalized_ctx:
        normalized_ctx["schedule_link"] = normalized_ctx["slot_link"]
    if "schedule_link" in normalized_ctx and "booking_link" not in normalized_ctx:
        normalized_ctx["booking_link"] = normalized_ctx["schedule_link"]
    if "job_description" in normalized_ctx and "job_details" not in normalized_ctx:
        normalized_ctx["job_details"] = normalized_ctx["job_description"]

    # Candidate name is globally mandatory
    if not normalized_ctx.get("candidate_name"):
        raise MissingTemplateVariablesError(
            f"Cannot send '{tmpl.name}'. Required variable 'candidate_name' is missing. Blocked and flagged for HR."
        )

    # Check which variables are present in the subject and body
    used_vars = extract_template_variable_placeholders(raw_subject).union(
        extract_template_variable_placeholders(raw_body)
    )

    missing: List[str] = []
    for var in used_vars:
        if var in SUPPORTED_VARIABLE_KEYS:
            val = normalized_ctx.get(var)
            if val is None or (isinstance(val, str) and not val.strip()):
                missing.append(var)

    if missing:
        raise MissingTemplateVariablesError(
            f"Cannot send '{tmpl.name}'. Required variable(s) {missing} used in template are missing or empty. Blocked and flagged for HR."
        )

    # Pure deterministic variable substitution. Never calls LLM.
    subject = fill_template_variables(raw_subject, normalized_ctx)
    text_body = fill_template_variables(raw_body, normalized_ctx)
    preheader = subject

    html_paragraphs = "".join(
        f"<p style='margin: 0 0 16px 0; line-height: 1.6;'>{p.strip()}</p>"
        for p in text_body.split("\n\n")
        if p.strip()
    )
    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{subject}</title></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-size: 14px; color: #1e293b; background-color: #f8fafc; padding: 24px;">
  <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 32px;">
    {html_paragraphs}
  </div>
</body>
</html>"""

    return subject, html_body, text_body, preheader


async def generate_recruiting_templates_ai(
    hr_name: Optional[str] = "Talent Team",
    company_name: Optional[str] = "Our Company",
    hr_role: Optional[str] = "Recruiter",
    email_tone: str = "warm_professional",
    single_template_key: Optional[str] = None,
) -> tuple[Dict[str, Dict[str, str]], bool, Optional[str], float]:
    """
    Calls AI model chain strictly for one-off authoring/regeneration in Settings.
    Never called at send time.
    """
    t0 = time.perf_counter()
    target_keys = (
        [single_template_key]
        if single_template_key and single_template_key in TEMPLATE_CONFIGS
        else list(TEMPLATE_CONFIGS.keys())
    )

    system_prompt = (
        "You are an elite corporate talent acquisition partner and master copywriter.\n"
        "Your task is to write authentic, short, warm, and human candidate email templates.\n\n"
        "STRICT TONE GUIDELINES:\n"
        f"- Target Tone: {(email_tone or 'warm_professional').replace('_', ' ').title()}\n"
        "- MUST BE SHORT, WARM AND HUMAN. NEVER ROBOTIC.\n"
        "- NEVER use cliché robotic phrases like 'I hope this email finds you well', 'Please find attached', "
        "'Per our discussion', or 'We regret to inform you'. Sound like a real recruiter having a thoughtful conversation.\n"
        "- Paragraphs must be short (1-3 sentences maximum).\n\n"
        "ALLOWED VARIABLES (only use tokens from this list in curly braces):\n"
        "  {candidate_name}, {role}, {company}, {hr_name}, {interview_date}, {interview_time}, "
        "{meet_link}, {schedule_link}, {job_details}\n\n"
        "REQUIRED KEYS TO GENERATE:\n"
        f"{', '.join(target_keys)}\n\n"
        "STRICT JSON OUTPUT FORMAT:\n"
        '{"templates": {"<key>": {"name": "<Friendly Name>", "subject": "<Subject line>", "body": "<Full body content>"}}}'
    )

    user_prompt = (
        f"Recruiter: {hr_name or 'Talent Lead'}\n"
        f"Company: {company_name or 'Our Company'}\n"
        f"Role: {hr_role or 'Recruiter'}\n"
        f"Tone: {email_tone}\n"
        f"Generate {len(target_keys)} template(s): {', '.join(target_keys)}."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        validated, model_used, latency = await ai_router.complete_with_chain(
            task_name="drafts",
            messages=messages,
            validation_schema=TemplatesBatchSchema,
            temperature=0.3,
        )

        result_templates: Dict[str, Dict[str, str]] = {}
        for k, v in validated.templates.items():
            cfg = TEMPLATE_CONFIGS.get(k, {})
            result_templates[k] = {
                "name": cfg.get("name", v.name or k.replace("_", " ").title()),
                "subject": v.subject.strip(),
                "body": v.body.strip(),
            }

        defaults = get_default_templates(
            hr_name=hr_name or "Talent Team",
            company_name=company_name or "Our Company",
            email_tone=email_tone,
        )
        for k in target_keys:
            if k not in result_templates:
                result_templates[k] = defaults[k]

        total_latency = time.perf_counter() - t0
        return result_templates, True, model_used, round(total_latency, 2)

    except Exception as exc:
        logger.warning("AI template generation encountered an error (%s). Falling back to human-crafted templates.", exc)
        defaults = get_default_templates(
            hr_name=hr_name or "Talent Team",
            company_name=company_name or "Our Company",
            email_tone=email_tone,
        )
        filtered = {k: defaults[k] for k in target_keys if k in defaults}
        total_latency = time.perf_counter() - t0
        return filtered, False, "human_crafted_fallback", round(total_latency, 2)
