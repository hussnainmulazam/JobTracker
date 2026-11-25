"""
app/services/ai.py
~~~~~~~~~~~~~~~~~~
AI integration for Candidate Screening, Interview Question Generation,
and Job Requirements Extraction powered by OpenRouter free tier models.
All requests are routed through app.services.ai_router.AIRouter.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.schemas.ai import (
    AIModelsHealthResponse,
    CandidateScreenLLMOutput,
    CVTailorLLMOutput,
    InterviewQuestionsLLMOutput,
    JobRequirementsExtractionOutput,
)
from app.services.ai_router import ai_router, clean_reasoning_and_extract_json

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Alias for backward compatibility
_clean_json_text = clean_reasoning_and_extract_json


async def _call_with_retry_and_fallback(
    task_name: str,
    primary_model: Optional[str] = None,
    fallback_model: Optional[str] = None,
    messages: List[Dict[str, str]] = None,
    validation_schema: Optional[Type[T]] = None,
) -> Tuple[Any, str, float]:
    """Backward-compatible proxy delegating directly to ai_router."""
    models = [m for m in [primary_model, fallback_model] if m] or None
    return await ai_router.complete_with_chain(
        task_name=task_name,
        messages=messages or [],
        validation_schema=validation_schema,
        models=models,
    )


# ── Job Requirements Extraction (JD Save) ────────────────────────────────────

async def extract_job_requirements(
    job_title: str,
    job_description: str,
) -> JobRequirementsExtractionOutput:
    """
    On JD save, calls OpenRouter extraction model chain to extract:
      - required_skills: List[str]
      - years_of_experience: Optional[float]
      - nice_to_haves: List[str]
    """
    import os
    if os.getenv("TESTING") == "true":
        return JobRequirementsExtractionOutput(
            required_skills=["Python", "FastAPI", "SQL"],
            years_of_experience=3.0,
            nice_to_haves=["Docker", "AWS"],
        )

    system_instruction = (
        "You are an elite corporate talent acquisition partner and senior technical recruiter.\n"
        "Your task is to analyze a Job Description (JD) and extract the key requirements into structured JSON.\n\n"
        "EXTRACTION RULES:\n"
        "1. required_skills: A list of core required technical or domain competencies explicitly required for the role.\n"
        "2. years_of_experience: A single float/int representing the minimum required years of experience (e.g. 3, 5.0). If not specified or entry level, return null.\n"
        "3. nice_to_haves: A list of bonus, preferred, or optional skills and tools.\n"
        "STRICT JSON OUTPUT: Return ONLY a valid JSON object matching the requested schema."
    )

    user_prompt = (
        f"--- JOB VACANCY ---\n"
        f"Title: {job_title}\n\n"
        f"Job Description:\n{job_description}\n\n"
        "Respond with a raw JSON object formatted exactly as:\n"
        "{\n"
        '  "required_skills": ["Python", "FastAPI", "SQL"],\n'
        '  "years_of_experience": 3.0,\n'
        '  "nice_to_haves": ["Docker", "Kubernetes", "AWS"]\n'
        "}"
    )

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_prompt},
    ]

    validated, model_used, latency = await ai_router.complete_with_chain(
        task_name="extraction",
        messages=messages,
        validation_schema=JobRequirementsExtractionOutput,
    )

    return validated


# ── Recruiter AI Candidate Screening Service ──────────────────────────────────

async def screen_candidate_cv(
    job_title: str,
    job_description: str,
    required_skills: List[str],
    candidate_name: str,
    cv_text: str,
) -> Dict[str, Any]:
    """
    Screen a candidate's CV against a Job Opening using the screening model chain.
    Calculates match score (0-100), matched skills, missing skills,
    red flags, executive summary, recommendation, and interview focus areas.
    """
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OpenRouter AI service is not configured. Missing OPENROUTER_API_KEY.",
        )

    system_instruction = (
        "You are an elite corporate talent acquisition partner and technical recruiter.\n"
        "Your task is to screen and evaluate a candidate's CV against a specific Job Opening.\n\n"
        "STRICT EVALUATION CRITERIA:\n"
        "1. OBJECTIVE SCORING (0-100): Score the candidate based strictly on demonstrated evidence in their CV "
        "relative to the job requirements, domain experience, and required skills.\n"
        "2. SKILL MATCH ANALYSIS:\n"
        "   - matched_skills: specific required or strongly relevant skills explicitly found in the CV.\n"
        "   - missing_skills: required skills or key requirements not evident or weak in the CV.\n"
        "3. RED FLAGS:\n"
        "   - red_flags: list potential concerns (e.g., unexplained gaps, missing mandatory qualifications, mismatch in seniority, lack of measurable accomplishments).\n"
        "4. EXECUTIVE SUMMARY: 2-4 sentences summarizing candidate background, strong points, and gaps.\n"
        "5. RECOMMENDATION: One of 'Strong Match', 'Potential Match', 'Review Needed', or 'Not a Fit'.\n"
        "6. INTERVIEW FOCUS AREAS: 2-4 targeted areas/questions to probe during the interview.\n"
        "7. STRICT JSON OUTPUT: Return ONLY a valid JSON object matching the requested schema."
    )

    req_skills_str = ", ".join(required_skills) if required_skills else "None specified"

    user_prompt = (
        f"--- TARGET JOB OPENING ---\n"
        f"Title: {job_title}\n"
        f"Required Skills: {req_skills_str}\n"
        f"Job Description:\n{job_description}\n\n"
        f"--- CANDIDATE CV ({candidate_name}) ---\n"
        f"{cv_text}\n\n"
        "Respond with a raw JSON object formatted exactly as:\n"
        "{\n"
        '  "score": 85.0,\n'
        '  "matched_skills": ["Skill1", "Skill2"],\n'
        '  "missing_skills": ["Skill3"],\n'
        '  "red_flags": ["Missing cloud deployment experience"],\n'
        '  "summary": "Candidate has solid experience in...",\n'
        '  "recommendation": "Strong Match",\n'
        '  "interview_focus_areas": ["Probe system design experience", "Verify familiarity with cloud CI/CD"]\n'
        "}"
    )

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_prompt},
    ]

    models = settings.get_models_for_task("screening")
    validated, model_used, latency = await ai_router.complete_with_chain(
        task_name="screening",
        messages=messages,
        validation_schema=CandidateScreenLLMOutput,
        models=models,
    )

    res_dict = {
        "score": round(float(validated.score), 1),
        "matched_skills": validated.matched_skills,
        "missing_skills": validated.missing_skills,
        "red_flags": validated.red_flags,
        "summary": validated.summary,
        "recommendation": validated.recommendation,
        "interview_focus_areas": validated.interview_focus_areas,
        "model_used": model_used,
        "latency_seconds": round(latency, 2),
    }

    return res_dict


async def generate_recruiter_interview_questions(
    job_title: Optional[str],
    job_description: str,
    candidate_cv: Optional[str] = None,
    red_flags: Optional[List[str]] = None,
    count: int = 5,
) -> List[str]:
    """
    Generate targeted interview questions using questions model chain.
    """
    if not settings.OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OpenRouter AI service is not configured. Missing OPENROUTER_API_KEY.",
        )

    system_instruction = (
        "You are a principal technical recruiter and interviewer.\n"
        "Generate insightful, high-signal interview questions for hiring managers to ask.\n"
        "Include a balanced mix of:\n"
        " - Technical verification of required skills\n"
        " - Deep-dive questions targeting identified red flags or missing skill areas\n"
        " - Architecture, scale, and problem-solving scenarios\n"
        " - Behavioral competency (ownership, teamwork, ambiguity)\n"
        "STRICT JSON OUTPUT: Output ONLY a single valid JSON object with the key 'questions' as a list of strings."
    )

    user_prompt = f"Role: {job_title or 'Target Role'}\nJob Description:\n{job_description}\n\n"
    if candidate_cv:
        user_prompt += f"Candidate CV:\n{candidate_cv}\n\n"
    if red_flags:
        user_prompt += "Identified Red Flags / Gaps:\n" + "\n".join(f"- {rf}" for rf in red_flags) + "\n\n"
    user_prompt += f"Generate {count} distinct interview questions in JSON format:\n" '{"questions": ["Question 1...", "Question 2..."]}'

    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_prompt},
    ]

    models = settings.get_models_for_task("questions")
    validated, model_used, latency = await ai_router.complete_with_chain(
        task_name="questions",
        messages=messages,
        validation_schema=InterviewQuestionsLLMOutput,
        models=models,
    )

    cleaned = [str(q).strip() for q in validated.questions if str(q).strip()]
    return cleaned[:count]


# ── Backward Compatible / Legacy AI functions ─────────────────────────────────

async def tailor_cv(base_cv: str, job_description: str) -> str:
    detailed = await tailor_cv_detailed(base_cv=base_cv, job_description=job_description)
    return detailed.get("tailored_cv", "")


async def tailor_cv_detailed(base_cv: str, job_description: str) -> Dict[str, Any]:
    system_instruction = (
        "You are an ATS optimization specialist. Rewrite the CV to align with the Job Description.\n"
        "Do NOT invent fake experience. Output valid JSON with keys: tailored_cv, matched_keywords, changes_summary."
    )
    user_prompt = (
        f"--- JD ---\n{job_description}\n\n--- CV ---\n{base_cv}\n\n"
        'JSON format: {"tailored_cv": "...", "matched_keywords": [], "changes_summary": "..."}'
    )
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": user_prompt},
    ]
    validated, model_used, latency = await ai_router.complete_with_chain(
        task_name="screening",
        messages=messages,
        validation_schema=CVTailorLLMOutput,
    )
    return {
        "tailored_cv": validated.tailored_cv,
        "matched_keywords": validated.matched_keywords,
        "changes_summary": validated.changes_summary,
        "model_used": model_used,
        "latency_seconds": round(latency, 2),
    }


async def generate_interview_questions(job_description: str, count: int = 5) -> List[str]:
    return await generate_recruiter_interview_questions(
        job_title=None,
        job_description=job_description,
        candidate_cv=None,
        count=count,
    )


# ── Health Check ──────────────────────────────────────────────────────────────

async def check_models_health() -> AIModelsHealthResponse:
    return await ai_router.check_health()
