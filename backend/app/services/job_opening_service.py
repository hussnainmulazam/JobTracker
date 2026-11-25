"""JobOpening service — business logic and DB operations for recruiter job openings."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import Session, func, select

from app.models.candidate import Candidate
from app.models.job_opening import JobOpening, JobOpeningStatus
from app.schemas.job_opening import (
    JobOpeningCreate,
    JobOpeningRead,
    JobOpeningUpdate,
    PaginatedJobOpenings,
)
from app.services.ai import extract_job_requirements
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class JobOpeningService:
    async def create(
        self,
        session: Session,
        user_id: uuid.UUID,
        data: JobOpeningCreate,
    ) -> JobOpeningRead:
        title = data.title.strip()
        description = data.description.strip()
        required_skills = data.required_skills
        years_of_experience = data.years_of_experience
        nice_to_haves = data.nice_to_haves or []

        # On JD save, call OpenRouter to extract required skills, years of experience, nice-to-haves
        try:
            extracted = await extract_job_requirements(
                job_title=title,
                job_description=description,
            )
            if not required_skills:
                required_skills = extracted.required_skills
            if years_of_experience is None:
                years_of_experience = extracted.years_of_experience
            if not nice_to_haves:
                nice_to_haves = extracted.nice_to_haves
        except Exception as exc:
            logger.warning("OpenRouter JD extraction on create failed or bypassed: %s", exc)
            if required_skills is None:
                required_skills = []

        opening = JobOpening(
            user_id=user_id,
            title=title,
            description=description,
            required_skills=required_skills or [],
            years_of_experience=years_of_experience,
            nice_to_haves=nice_to_haves or [],
            status=data.status,
        )
        session.add(opening)
        session.commit()
        session.refresh(opening)

        # Invalidate requisition list cache for this recruiter
        cache_service.delete_prefix(f"requisition:list:{user_id}")

        read = JobOpeningRead.model_validate(opening)
        read.candidates_count = 0
        cache_service.set(f"requisition:detail:{opening.id}", read.model_dump(), ttl=180)
        return read

    def get_by_id(
        self,
        session: Session,
        user_id: uuid.UUID,
        opening_id: uuid.UUID,
    ) -> JobOpening:
        statement = select(JobOpening).where(
            JobOpening.id == opening_id,
            JobOpening.user_id == user_id,
        )
        opening = session.exec(statement).first()
        if not opening:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job opening '{opening_id}' not found.",
            )
        return opening

    def get_read_by_id(
        self,
        session: Session,
        user_id: uuid.UUID,
        opening_id: uuid.UUID,
    ) -> JobOpeningRead:
        opening = self.get_by_id(session, user_id, opening_id)
        cache_key = f"requisition:detail:{user_id}:{opening_id}"
        cached = cache_service.get(cache_key)
        if cached is not None:
            return JobOpeningRead.model_validate(cached)

        count_stmt = select(func.count(Candidate.id)).where(Candidate.opening_id == opening_id)
        candidates_count = session.exec(count_stmt).one() or 0

        read = JobOpeningRead.model_validate(opening)
        read.candidates_count = candidates_count
        cache_service.set(cache_key, read.model_dump(), ttl=180)
        return read

    def list(
        self,
        session: Session,
        user_id: uuid.UUID,
        status_filter: Optional[JobOpeningStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> PaginatedJobOpenings:
        query = select(JobOpening).where(JobOpening.user_id == user_id)

        if status_filter:
            query = query.where(JobOpening.status == status_filter)

        if search:
            query = query.where(JobOpening.title.ilike(f"%{search.strip()}%"))

        count_stmt = select(func.count()).select_from(query.subquery())
        total = session.exec(count_stmt).one() or 0

        query = query.order_by(JobOpening.created_at.desc()).offset(skip).limit(limit)
        items = session.exec(query).all()

        read_items: list[JobOpeningRead] = []
        for it in items:
            c_count = (
                session.exec(
                    select(func.count(Candidate.id)).where(Candidate.opening_id == it.id)
                ).one()
                or 0
            )
            r = JobOpeningRead.model_validate(it)
            r.candidates_count = c_count
            read_items.append(r)

        return PaginatedJobOpenings(
            items=read_items,
            total=total,
            skip=skip,
            limit=limit,
        )

    async def update(
        self,
        session: Session,
        user_id: uuid.UUID,
        opening_id: uuid.UUID,
        data: JobOpeningUpdate,
    ) -> JobOpeningRead:
        opening = self.get_by_id(session, user_id, opening_id)

        update_dict = data.model_dump(exclude_unset=True)
        if "title" in update_dict and update_dict["title"]:
            update_dict["title"] = update_dict["title"].strip()
        if "description" in update_dict and update_dict["description"]:
            update_dict["description"] = update_dict["description"].strip()

        # On JD update, call OpenRouter to re-extract requirements if description is updated and skills not provided
        if "description" in update_dict and "required_skills" not in update_dict:
            try:
                title = update_dict.get("title", opening.title)
                desc = update_dict["description"]
                extracted = await extract_job_requirements(job_title=title, job_description=desc)
                update_dict["required_skills"] = extracted.required_skills
                if "years_of_experience" not in update_dict:
                    update_dict["years_of_experience"] = extracted.years_of_experience
                if "nice_to_haves" not in update_dict:
                    update_dict["nice_to_haves"] = extracted.nice_to_haves
            except Exception as exc:
                logger.warning("OpenRouter JD extraction on update failed: %s", exc)

        for key, value in update_dict.items():
            setattr(opening, key, value)

        opening.updated_at = datetime.now(timezone.utc)
        session.add(opening)
        session.commit()
        session.refresh(opening)

        # Invalidate requisition detail and list caches
        cache_service.delete(f"requisition:detail:{opening.id}")
        cache_service.delete_prefix(f"requisition:list:{user_id}")

        return self.get_read_by_id(session, user_id, opening.id)

    def delete(
        self,
        session: Session,
        user_id: uuid.UUID,
        opening_id: uuid.UUID,
    ) -> None:
        opening = self.get_by_id(session, user_id, opening_id)
        session.delete(opening)
        session.commit()

        # Invalidate requisition detail and list caches
        cache_service.delete(f"requisition:detail:{opening_id}")
        cache_service.delete_prefix(f"requisition:list:{user_id}")


job_opening_service = JobOpeningService()
