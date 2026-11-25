"""
backend/app/routers/recruiting_templates.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
REST endpoints for managing database-backed recruiting email templates.
Single source of truth for candidate communication templates.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.core.dependencies import get_current_user, get_session
from app.models.recruiting_template import RecruitingTemplate
from app.models.user import User
from app.services.template_service import (
    clear_user_template_cache,
    generate_recruiting_templates_ai,
    get_user_templates_from_db,
    TEMPLATE_CONFIGS,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/recruiting-templates",
    tags=["Recruiting Templates"],
)


class TemplateCatalogItem(BaseModel):
    id: str
    name: str
    category: str
    subject: str
    preheader: Optional[str] = None
    body: str
    html_content: Optional[str] = None
    required_variables: List[str] = []
    trigger_event: Optional[str] = None


class TemplateResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    stage_key: str
    name: str
    description: Optional[str] = None
    subject: str
    body: str
    is_active: bool
    is_default: bool
    is_custom: bool
    created_at: datetime
    updated_at: datetime


class TemplateCreateRequest(BaseModel):
    stage_key: str
    name: str
    description: Optional[str] = None
    subject: str = Field(..., min_length=2)
    body: str = Field(..., min_length=5)
    is_active: bool = True
    is_default: bool = False
    is_custom: bool = True


class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class BatchSaveRequest(BaseModel):
    templates: Dict[str, Dict[str, Any]]


class RegenerateAIRequest(BaseModel):
    single_template_key: Optional[str] = None


@router.get("", response_model=List[TemplateResponse])
def list_templates(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Returns all recruiting templates for current user strictly from DB.
    Seeds missing defaults once per user, preserving HR edits.
    """
    templates = get_user_templates_from_db(session, current_user.id)
    return templates


@router.get("/catalog", response_model=List[TemplateCatalogItem])
def get_template_catalog(
    current_user: User = Depends(get_current_user),
):
    """
    Returns all 31 production email templates from templates/registry.json
    categorized by core, supporting, and internal.
    """
    from app.services.pipeline_template_service import get_registry, REGISTRY_PATH
    registry = get_registry()
    templates_map = registry.get("templates", {})
    categories = registry.get("categories", {})

    cat_lookup = {}
    for cat, t_ids in categories.items():
        for tid in t_ids:
            cat_lookup[tid] = cat

    tpl_dir = os.path.dirname(REGISTRY_PATH) if os.path.exists(REGISTRY_PATH) else os.path.abspath("templates")
    results = []
    for tid, meta in templates_map.items():
        cat = cat_lookup.get(tid, "core")
        txt_file = os.path.join(tpl_dir, f"{tid}.txt")
        html_file = os.path.join(tpl_dir, f"{tid}.html")

        body = ""
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                body = f.read().strip()

        html_content = ""
        if os.path.exists(html_file):
            with open(html_file, "r", encoding="utf-8") as f:
                html_content = f.read()

        results.append(
            TemplateCatalogItem(
                id=tid,
                name=meta.get("id", tid).replace("_", " ").title(),
                category=cat,
                subject=meta.get("subject", ""),
                preheader=meta.get("preheader"),
                body=body,
                html_content=html_content,
                required_variables=meta.get("required_variables", []),
                trigger_event=meta.get("trigger_event"),
            )
        )
    return results


@router.get("/detail/{name_or_id}")
def get_template_by_name_or_id(
    name_or_id: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Fetches a template by UUID or by template name (e.g. cv_received).
    """
    # 1. Try UUID in database
    try:
        tmpl_uuid = uuid.UUID(name_or_id)
        db_tmpl = session.exec(
            select(RecruitingTemplate).where(
                RecruitingTemplate.id == tmpl_uuid,
                RecruitingTemplate.user_id == current_user.id,
            )
        ).first()
        if db_tmpl:
            return db_tmpl
    except ValueError:
        pass

    # 2. Try stage_key in database
    db_tmpl = session.exec(
        select(RecruitingTemplate).where(
            RecruitingTemplate.stage_key == name_or_id,
            RecruitingTemplate.user_id == current_user.id,
            RecruitingTemplate.is_default == True,
        )
    ).first()
    if db_tmpl:
        return db_tmpl

    # 3. Fallback to templates/registry.json
    from app.services.pipeline_template_service import get_registry, REGISTRY_PATH
    registry = get_registry()
    templates_map = registry.get("templates", {})
    if name_or_id in templates_map:
        meta = templates_map[name_or_id]
        tpl_dir = os.path.dirname(REGISTRY_PATH) if os.path.exists(REGISTRY_PATH) else os.path.abspath("templates")
        txt_file = os.path.join(tpl_dir, f"{name_or_id}.txt")
        html_file = os.path.join(tpl_dir, f"{name_or_id}.html")
        body = ""
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                body = f.read().strip()
        html_content = ""
        if os.path.exists(html_file):
            with open(html_file, "r", encoding="utf-8") as f:
                html_content = f.read()

        return {
            "id": name_or_id,
            "stage_key": name_or_id,
            "name": name_or_id.replace("_", " ").title(),
            "subject": meta.get("subject", ""),
            "body": body,
            "html_content": html_content,
            "is_active": True,
            "is_default": True,
            "is_custom": False,
        }

    raise HTTPException(status_code=404, detail=f"Template '{name_or_id}' not found")


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: TemplateCreateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Creates a new recruiting template."""
    now = datetime.now(timezone.utc)
    new_tmpl = RecruitingTemplate(
        user_id=current_user.id,
        stage_key=payload.stage_key.strip(),
        name=payload.name.strip(),
        description=payload.description,
        subject=payload.subject.strip(),
        body=payload.body.strip(),
        is_active=payload.is_active,
        is_default=payload.is_default,
        is_custom=payload.is_custom,
        created_at=now,
        updated_at=now,
    )
    session.add(new_tmpl)
    session.commit()
    session.refresh(new_tmpl)
    clear_user_template_cache(current_user.id)
    return new_tmpl


@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: uuid.UUID,
    payload: TemplateUpdateRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Updates an existing template and clears cache."""
    tmpl = session.exec(
        select(RecruitingTemplate).where(
            RecruitingTemplate.id == template_id,
            RecruitingTemplate.user_id == current_user.id,
        )
    ).first()

    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id {template_id} not found",
        )

    if payload.name is not None:
        tmpl.name = payload.name.strip()
    if payload.description is not None:
        tmpl.description = payload.description.strip()
    if payload.subject is not None:
        tmpl.subject = payload.subject.strip()
    if payload.body is not None:
        tmpl.body = payload.body.strip()
    if payload.is_active is not None:
        tmpl.is_active = payload.is_active
    if payload.is_default is not None:
        if payload.is_default:
            # Unset default on other templates for this stage
            others = session.exec(
                select(RecruitingTemplate).where(
                    RecruitingTemplate.user_id == current_user.id,
                    RecruitingTemplate.stage_key == tmpl.stage_key,
                    RecruitingTemplate.id != tmpl.id,
                )
            ).all()
            for other in others:
                other.is_default = False
                session.add(other)
        tmpl.is_default = payload.is_default

    tmpl.updated_at = datetime.now(timezone.utc)
    session.add(tmpl)
    session.commit()
    session.refresh(tmpl)
    clear_user_template_cache(current_user.id)
    return tmpl


@router.post("/{template_id}/duplicate", response_model=TemplateResponse)
def duplicate_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Duplicates a template with is_custom=True and clears cache."""
    tmpl = session.exec(
        select(RecruitingTemplate).where(
            RecruitingTemplate.id == template_id,
            RecruitingTemplate.user_id == current_user.id,
        )
    ).first()

    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id {template_id} not found",
        )

    now = datetime.now(timezone.utc)
    clone = RecruitingTemplate(
        user_id=current_user.id,
        stage_key=tmpl.stage_key,
        name=f"Copy of {tmpl.name}",
        description=tmpl.description,
        subject=tmpl.subject,
        body=tmpl.body,
        is_active=True,
        is_default=False,
        is_custom=True,
        created_at=now,
        updated_at=now,
    )
    session.add(clone)
    session.commit()
    session.refresh(clone)
    clear_user_template_cache(current_user.id)
    return clone


@router.post("/{template_id}/toggle", response_model=TemplateResponse)
def toggle_template_active(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Toggles template active state and clears cache."""
    tmpl = session.exec(
        select(RecruitingTemplate).where(
            RecruitingTemplate.id == template_id,
            RecruitingTemplate.user_id == current_user.id,
        )
    ).first()

    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id {template_id} not found",
        )

    tmpl.is_active = not tmpl.is_active
    tmpl.updated_at = datetime.now(timezone.utc)
    session.add(tmpl)
    session.commit()
    session.refresh(tmpl)
    clear_user_template_cache(current_user.id)
    return tmpl


@router.post("/{template_id}/set-default", response_model=TemplateResponse)
def set_template_default(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Sets a template as default for its stage key and clears cache."""
    tmpl = session.exec(
        select(RecruitingTemplate).where(
            RecruitingTemplate.id == template_id,
            RecruitingTemplate.user_id == current_user.id,
        )
    ).first()

    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id {template_id} not found",
        )

    others = session.exec(
        select(RecruitingTemplate).where(
            RecruitingTemplate.user_id == current_user.id,
            RecruitingTemplate.stage_key == tmpl.stage_key,
        )
    ).all()

    for other in others:
        other.is_default = (other.id == tmpl.id)
        session.add(other)

    tmpl.is_default = True
    tmpl.updated_at = datetime.now(timezone.utc)
    session.add(tmpl)
    session.commit()
    session.refresh(tmpl)
    clear_user_template_cache(current_user.id)
    return tmpl


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Deletes a custom template and clears cache."""
    tmpl = session.exec(
        select(RecruitingTemplate).where(
            RecruitingTemplate.id == template_id,
            RecruitingTemplate.user_id == current_user.id,
        )
    ).first()

    if not tmpl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id {template_id} not found",
        )

    session.delete(tmpl)
    session.commit()
    clear_user_template_cache(current_user.id)
    return None


@router.post("/batch")
def batch_save_templates(
    payload: BatchSaveRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Saves/updates multiple templates in bulk.
    Updates existing rows in recruiting_templates and clears cache.
    """
    existing = session.exec(
        select(RecruitingTemplate).where(RecruitingTemplate.user_id == current_user.id)
    ).all()
    by_stage: Dict[str, RecruitingTemplate] = {t.stage_key: t for t in existing if t.is_default}
    # Also index all existing by id if id is provided
    by_id: Dict[uuid.UUID, RecruitingTemplate] = {t.id: t for t in existing}

    now = datetime.now(timezone.utc)
    for key, data in payload.templates.items():
        tmpl_id = data.get("id")
        target: Optional[RecruitingTemplate] = None
        if tmpl_id:
            try:
                target = by_id.get(uuid.UUID(str(tmpl_id)))
            except Exception:
                pass
        if not target:
            target = by_stage.get(key)

        if target:
            target.subject = data.get("subject", target.subject).strip()
            target.body = data.get("body", target.body).strip()
            if data.get("name"):
                target.name = data["name"].strip()
            if "is_active" in data:
                target.is_active = bool(data["is_active"])
            target.updated_at = now
            session.add(target)
        else:
            cfg = TEMPLATE_CONFIGS.get(key, {})
            new_tmpl = RecruitingTemplate(
                user_id=current_user.id,
                stage_key=key,
                name=data.get("name") or cfg.get("name", key.replace("_", " ").title()),
                description=cfg.get("description", ""),
                subject=data.get("subject", "").strip(),
                body=data.get("body", "").strip(),
                is_active=data.get("is_active", True),
                is_default=True,
                is_custom=False,
                created_at=now,
                updated_at=now,
            )
            session.add(new_tmpl)

    session.commit()
    clear_user_template_cache(current_user.id)
    return {"message": "Templates saved successfully to database", "count": len(payload.templates)}


@router.post("/regenerate")
async def regenerate_templates_ai(
    payload: RegenerateAIRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    One-click AI generator/regenerator in Settings.
    Does NOT call AI at email send time; purely for drafting templates in Settings.
    """
    hr_name = "Recruiter"
    company_name = "Our Company"
    hr_role = "Recruiting Lead"
    email_tone = "warm_professional"

    try:
        from app.models.onboarding import OnboardingSetup
        onboarding = session.exec(
            select(OnboardingSetup).where(OnboardingSetup.user_id == current_user.id)
        ).first()
        if onboarding:
            if onboarding.hr_name:
                hr_name = onboarding.hr_name
            if onboarding.company_name:
                company_name = onboarding.company_name
            if onboarding.hr_role:
                hr_role = onboarding.hr_role
            if onboarding.email_tone:
                email_tone = onboarding.email_tone
    except Exception as exc:
        logger.debug("Could not fetch onboarding profile for AI generation: %s", exc)

    templates, success, model_used, latency = await generate_recruiting_templates_ai(
        hr_name=hr_name,
        company_name=company_name,
        hr_role=hr_role,
        email_tone=email_tone,
        single_template_key=payload.single_template_key,
    )

    clear_user_template_cache(current_user.id)
    return {
        "templates": templates,
        "success": success,
        "model_used": model_used,
        "latency_seconds": latency,
    }
