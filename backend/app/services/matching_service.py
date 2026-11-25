"""
Backward-compatible alias module for app.services.ai.
"""
from app.services.ai import (
    screen_candidate_cv,
    generate_recruiter_interview_questions,
    check_models_health,
    tailor_cv,
    tailor_cv_detailed,
)

__all__ = [
    "screen_candidate_cv",
    "generate_recruiter_interview_questions",
    "check_models_health",
    "tailor_cv",
    "tailor_cv_detailed",
]
