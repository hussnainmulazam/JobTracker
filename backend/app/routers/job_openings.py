"""
app/routers/job_openings.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
CRUD, JD OpenRouter skill extraction, Background CV matching with caching,
Bulk AI candidate scoring with ranking, Shortlist CSV export,
and screening question generation for Recruiter Job Openings.

All routes require authentication (CurrentUser) and are strictly scoped
to the authenticated recruiter — ownership is enforced at the service layer.
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Query, Response, status

from app.core.dependencies import CurrentUser
from app.db import SessionDep
from app.models.candidate import Candidate, CandidateStage
from app.models.job_opening import JobOpeningStatus
from app.schemas.candidate import BulkScoreResponse
from app.schemas.extractor import CandidateExtractedDetails, GoogleSheetSyncResponse
from app.schemas.job_opening import (
    JobOpeningCreate,
    JobOpeningRead,
    JobOpeningUpdate,
    MatchProgressStatus,
    PaginatedJobOpenings,
)
from app.schemas.ai import RecruiterInterviewQuestionsResponse
from app.services.ai import generate_recruiter_interview_questions
from app.services.candidate_service import candidate_service
from app.services.extractor_service import extractor_service
from app.services.google_sheets_service import google_sheets_service
from app.services.job_opening_service import job_opening_service
from sqlmodel import select

router = APIRouter(prefix="/job-openings", tags=["Job Openings"])
openings_alias_router = APIRouter(prefix="/openings", tags=["Job Openings"])


# ── Create Job Opening (with OpenRouter JD extraction) ────────────────────────

@router.post(
    "",
    response_model=JobOpeningRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job opening (auto-extracts required skills & experience via AI)",
)
@openings_alias_router.post(
    "",
    response_model=JobOpeningRead,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_job_opening(
    body: JobOpeningCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> JobOpeningRead:
    """
    Create a new job opening.
    On JD save, calls OpenRouter to extract required skills, years of experience,
    and nice-to-haves (strict JSON, Pydantic-validated).
    """
    return await job_opening_service.create(
        session=session,
        user_id=current_user.id,
        data=body,
    )


# ── List Job Openings ─────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedJobOpenings,
    status_code=status.HTTP_200_OK,
    summary="List job openings",
)
@openings_alias_router.get(
    "",
    response_model=PaginatedJobOpenings,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def list_job_openings(
    session: SessionDep,
    current_user: CurrentUser,
    status_filter: Optional[JobOpeningStatus] = Query(default=None, alias="status"),
    search: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
) -> PaginatedJobOpenings:
    """List all job openings created by the authenticated recruiter."""
    return job_opening_service.list(
        session=session,
        user_id=current_user.id,
        status_filter=status_filter,
        search=search,
        skip=skip,
        limit=limit,
    )


# ── Get Job Opening by ID ─────────────────────────────────────────────────────

@router.get(
    "/{opening_id}",
    response_model=JobOpeningRead,
    status_code=status.HTTP_200_OK,
    summary="Get a job opening by ID",
)
@openings_alias_router.get(
    "/{opening_id}",
    response_model=JobOpeningRead,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def get_job_opening(
    opening_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> JobOpeningRead:
    """Get single job opening details."""
    return job_opening_service.get_read_by_id(
        session=session,
        user_id=current_user.id,
        opening_id=opening_id,
    )


# ── Update Job Opening ────────────────────────────────────────────────────────

@router.patch(
    "/{opening_id}",
    response_model=JobOpeningRead,
    status_code=status.HTTP_200_OK,
    summary="Update a job opening",
)
@openings_alias_router.patch(
    "/{opening_id}",
    response_model=JobOpeningRead,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def update_job_opening(
    opening_id: uuid.UUID,
    body: JobOpeningUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> JobOpeningRead:
    """Update fields of a job opening. Re-extracts requirements if JD is updated."""
    return await job_opening_service.update(
        session=session,
        user_id=current_user.id,
        opening_id=opening_id,
        data=body,
    )


# ── Delete Job Opening ────────────────────────────────────────────────────────

@router.delete(
    "/{opening_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a job opening",
)
@openings_alias_router.delete(
    "/{opening_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    include_in_schema=False,
)
def delete_job_opening(
    opening_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> None:
    """Delete a job opening and its associated candidates and scorecards."""
    job_opening_service.delete(
        session=session,
        user_id=current_user.id,
        opening_id=opening_id,
    )


# ── Background Matching: POST /openings/{id}/match ───────────────────────────

@router.post(
    "/{opening_id}/match",
    response_model=MatchProgressStatus,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Score every unmatched CV (0-100) with matched/missing skills, red flags & reason",
)
@openings_alias_router.post(
    "/{opening_id}/match",
    response_model=MatchProgressStatus,
    status_code=status.HTTP_202_ACCEPTED,
    include_in_schema=False,
)
async def match_candidates_for_opening(
    opening_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    session: SessionDep,
    current_user: CurrentUser,
    rerun: bool = Query(default=False, description="If True, re-evaluates all candidates even if previously scored"),
) -> MatchProgressStatus:
    """
    Score every unmatched CV (0-100) with matched_skills, missing_skills,
    red_flags, and one-paragraph reason. Caches results and processes in the background.
    """
    # Verify opening exists and belongs to recruiter
    job_opening_service.get_by_id(session, current_user.id, opening_id)

    candidates = session.exec(
        select(Candidate).where(
            Candidate.opening_id == opening_id,
            Candidate.user_id == current_user.id,
        )
    ).all()

    matched_count = 0
    for cand in candidates:
        if rerun or cand.score is None:
            await candidate_service.score_candidate(session, current_user.id, cand.id, re_run=rerun)
            matched_count += 1
        else:
            matched_count += 1

    total = len(candidates)
    pct = (matched_count / total * 100.0) if total > 0 else 100.0

    return MatchProgressStatus(
        opening_id=opening_id,
        status="in_progress",
        total_candidates=total,
        processed_candidates=matched_count,
        matched_candidates=matched_count,
        progress_percent=round(pct, 1),
        errors=[],
    )


@router.get(
    "/{opening_id}/match/status",
    response_model=MatchProgressStatus,
    summary="Get background matching progress status for an opening",
)
@openings_alias_router.get(
    "/{opening_id}/match/status",
    response_model=MatchProgressStatus,
    include_in_schema=False,
)
def get_matching_progress(
    opening_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> MatchProgressStatus:
    """Check the real-time background progress of CV matching for an opening."""
    job_opening_service.get_by_id(session, current_user.id, opening_id)
    candidates = session.exec(
        select(Candidate).where(
            Candidate.opening_id == opening_id,
            Candidate.user_id == current_user.id,
        )
    ).all()
    matched = sum(1 for c in candidates if c.score is not None)
    total = len(candidates)
    pct = (matched / total * 100.0) if total > 0 else 100.0
    return MatchProgressStatus(
        opening_id=opening_id,
        status="completed" if (total > 0 and matched == total) else "in_progress",
        total_candidates=total,
        processed_candidates=matched,
        matched_candidates=matched,
        progress_percent=round(pct, 1),
        errors=[],
    )


# ── Bulk Score Candidates (Sync Ranking) ──────────────────────────────────────

@router.post(
    "/{opening_id}/bulk-score",
    response_model=BulkScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Bulk score all candidates for this opening and return them ranked",
)
@openings_alias_router.post(
    "/{opening_id}/bulk-score",
    response_model=BulkScoreResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def bulk_score_candidates(
    opening_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    candidate_ids: Optional[List[uuid.UUID]] = None,
) -> BulkScoreResponse:
    """
    Score all candidates under this job opening using OpenRouter.
    Returns candidates sorted and ranked by fit score descending.
    """
    return await candidate_service.bulk_score_opening(
        session=session,
        user_id=current_user.id,
        opening_id=opening_id,
        candidate_ids=candidate_ids,
    )


# ── Shortlist CSV Export ──────────────────────────────────────────────────────

@router.get(
    "/{opening_id}/shortlist/export",
    status_code=status.HTTP_200_OK,
    summary="Export shortlisted and screened candidates as CSV",
    response_class=Response,
)
@openings_alias_router.get(
    "/{opening_id}/shortlist/export",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
    response_class=Response,
)
def export_shortlist(
    opening_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    min_score: Optional[float] = Query(default=None, ge=0.0, le=100.0),
    stage: Optional[CandidateStage] = Query(default=None),
) -> Response:
    """
    Export ranked candidate shortlist as a CSV file with full screening metadata
    (Rank, Name, Email, Fit Score, Matched Skills, Missing Skills, Red Flags, Summary).
    """
    csv_content = candidate_service.export_shortlist_csv(
        session=session,
        user_id=current_user.id,
        opening_id=opening_id,
        min_score=min_score,
        stage=stage,
    )

    filename = f"shortlist_{opening_id}.csv"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "text/csv; charset=utf-8",
    }
    return Response(content=csv_content, media_type="text/csv", headers=headers)


# ── Screening Question Generation ─────────────────────────────────────────────

@router.post(
    "/{opening_id}/screening-questions",
    response_model=RecruiterInterviewQuestionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate screening questions for this job opening",
)
@openings_alias_router.post(
    "/{opening_id}/screening-questions",
    response_model=RecruiterInterviewQuestionsResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def generate_opening_screening_questions(
    opening_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    count: int = Query(default=5, ge=1, le=15),
) -> RecruiterInterviewQuestionsResponse:
    """Generate targeted screening questions based on the job opening's description."""
    opening = job_opening_service.get_by_id(session, current_user.id, opening_id)
    questions = await generate_recruiter_interview_questions(
        job_title=opening.title,
        job_description=opening.description,
        count=count,
    )
    return RecruiterInterviewQuestionsResponse(questions=questions)


# ── Google Sheets Candidate Sync ──────────────────────────────────────────────

@router.post(
    "/{opening_id}/sync-google-sheet",
    response_model=GoogleSheetSyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or upsert candidate shortlist rows into Google Spreadsheet",
)
@openings_alias_router.post(
    "/{opening_id}/sync-google-sheet",
    response_model=GoogleSheetSyncResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def sync_opening_candidates_to_google_sheet(
    opening_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> GoogleSheetSyncResponse:
    """
    Sync shortlisted candidates to Google Sheets:
      - Creates a Google Spreadsheet for the opening (if not already existing)
      - Upserts rows by candidate ID keeping column layout stable
      - Preserves live link to spreadsheet in opening record
    """
    return await google_sheets_service.sync_opening_candidates_to_sheet(
        session=session,
        opening_id=opening_id,
        user_id=current_user.id,
    )


# ── Batch Extract Details for Opening Candidates ──────────────────────────────

@router.post(
    "/{opening_id}/extract-all",
    response_model=List[CandidateExtractedDetails],
    status_code=status.HTTP_200_OK,
    summary="Extract details & online profiles for all candidates in this opening",
)
@openings_alias_router.post(
    "/{opening_id}/extract-all",
    response_model=List[CandidateExtractedDetails],
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def extract_all_opening_candidates(
    opening_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    verify_urls: bool = Query(default=True),
) -> List[CandidateExtractedDetails]:
    """Batch extracts contact and online profile links for all candidates under an opening."""
    candidates = session.exec(
        select(Candidate).where(
            Candidate.opening_id == opening_id,
            Candidate.user_id == current_user.id,
        )
    ).all()

    results: List[CandidateExtractedDetails] = []
    for c in candidates:
        res = await extractor_service.extract_candidate_details(
            session=session,
            candidate_id=c.id,
            user_id=current_user.id,
            verify_urls=verify_urls,
        )
        results.append(res)
    return results
