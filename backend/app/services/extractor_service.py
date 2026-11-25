"""
Candidate Detail Extractor Service.
Extracts contact details, professional links, title, experience, skills, and education
using Regex and Heuristics FIRST, then OpenRouter LLM for gap-filling.

Never invents values; leaves null if absent.
Stores confidence (0.0 to 1.0) and source ('regex', 'heuristic', 'llm') per field.
Includes duplicate detection against real database.
"""
import asyncio
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx
from sqlmodel import Session, select

from app.core.config import settings
from app.models.candidate import Candidate
from app.models.candidate_link import CandidateLink
from app.models.job_opening import JobOpening
from app.schemas.extractor import (
    CandidateDuplicateInfo,
    CandidateExtractedDetails,
    CandidateExtractionLLMOutput,
    CandidateExtractionPreviewResponse,
    ExtractedCandidateData,
    ExtractedFieldMeta,
)
from app.services.ai_router import ai_router

logger = logging.getLogger(__name__)

# ── Regex Patterns ───────────────────────────────────────────────────────────
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_REGEX = re.compile(
    r"(?:(?:\+|00)\d{1,4}[-.\s]*)?(?:\(?\d{2,5}\)?[-.\s]*)?\d{3,4}[-.\s]?\d{3,5}(?:[-.\s]?\d{2,5})?"
)
GITHUB_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_-]{2,39})(?:/[a-zA-Z0-9_.-]+)?/?",
    re.IGNORECASE,
)
LINKEDIN_REGEX = re.compile(
    r"(?:https?://)?(?:[a-z]{2,3}\.)?linkedin\.com/in/([a-zA-Z0-9%_-]{3,100})/?",
    re.IGNORECASE,
)
KAGGLE_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?kaggle\.com/([a-zA-Z0-9_-]{3,50})/?",
    re.IGNORECASE,
)
GENERIC_URL_REGEX = re.compile(
    r"https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_+.~#?&/=]*)",
    re.IGNORECASE,
)
YEARS_EXP_REGEX = re.compile(
    r"(?i)\b(\d{1,2}(?:\.\d)?)\+?\s*(?:years?|yrs?)\b(?:\s+of)?(?:\s+professional|\s+relevant|\s+industry)?\s+(?:experience|exp)\b"
)
EDUCATION_DEGREE_REGEX = re.compile(
    r"(?i)\b(bachelor(?:'s)?|master(?:'s)?|doctorate|ph\.?d\.?|b\.?s\.?c?|m\.?s\.?c?|b\.?a\.?|m\.?a\.?|m\.?b\.?a\.?|b\.?e\.?|b\.?tech|m\.?tech|associate(?:'s)?)\b(?:\s+(?:degree|of|in)\s+([a-zA-Z\s&,]+))?",
)

# Curated skill lexicon for deterministic matching
STANDARD_SKILLS: List[str] = [
    # Languages
    "Python", "JavaScript", "TypeScript", "Go", "Golang", "Rust", "Java", "C++", "C#", "PHP",
    "Ruby", "Swift", "Kotlin", "Scala", "SQL", "HTML", "CSS", "Bash", "Shell",
    # Frontend
    "React", "React Native", "Next.js", "Vue", "Vue.js", "Nuxt.js", "Angular", "Svelte",
    "Tailwind CSS", "Redux", "GraphQL", "Webpack", "Vite",
    # Backend & Frameworks
    "Node.js", "Express", "FastAPI", "Django", "Flask", "Spring Boot", "ASP.NET", ".NET",
    "Laravel", "Ruby on Rails", "NestJS", "gRPC", "REST API",
    # Cloud & DevOps
    "AWS", "Amazon Web Services", "GCP", "Google Cloud", "Azure", "Docker", "Kubernetes",
    "Terraform", "CI/CD", "Linux", "Git", "GitHub Actions", "Jenkins", "Ansible", "Prometheus", "Grafana",
    # Databases & Storage
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "SQLite", "DynamoDB",
    "Cassandra", "Supabase", "Firebase",
    # AI / ML / Data
    "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "Pandas", "NumPy",
    "Scikit-learn", "NLP", "Computer Vision", "OpenCV", "LLMs", "Generative AI", "LangChain",
    # Architecture & Practices
    "Microservices", "System Design", "Agile", "Scrum", "TDD", "Unit Testing",
]

# Standard titles lexicon for heuristic detection
TITLE_KEYWORDS = [
    "Software Engineer", "Frontend Engineer", "Backend Engineer", "Full Stack Engineer",
    "Full-Stack Developer", "Software Developer", "DevOps Engineer", "Cloud Architect",
    "Data Scientist", "Data Engineer", "Machine Learning Engineer", "AI Researcher",
    "Product Manager", "Project Manager", "Engineering Manager", "Technical Lead",
    "Solutions Architect", "UI/UX Designer", "Product Designer", "QA Engineer",
    "Security Engineer", "Database Administrator", "Site Reliability Engineer",
]


def _normalize_url(url: str, default_domain: str = "") -> str:
    """Ensure URL has https:// prefix."""
    clean = url.strip().rstrip(".,;)")
    if clean.startswith("http://") or clean.startswith("https://"):
        return clean
    if default_domain and not clean.startswith(default_domain):
        return f"https://{default_domain}/{clean.lstrip('/')}"
    return f"https://{clean}"


# ── 1. Name Heuristic Extraction ─────────────────────────────────────────────

def extract_name_heuristic(text: str) -> Tuple[Optional[str], float, str]:
    """
    Extract candidate full name from top lines of CV text using heuristics:
    - Scans the first 6 non-empty lines.
    - Rejects lines containing '@', URLs, phone digits, colons, or generic resume words.
    - Requires 2-4 words, starts with uppercase letters, length between 3 and 45 characters.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return (None, 0.0, "heuristic")

    ignore_words = {
        "resume", "cv", "curriculum", "vitae", "profile", "summary", "contact",
        "experience", "education", "skills", "projects", "phone", "email",
        "address", "linkedin", "github", "page", "developer", "engineer"
    }

    for line in lines[:6]:
        # Filter out lines that look like headers, contact lines, or labels
        lower = line.lower()
        if "@" in line or "http" in lower or ".com" in lower or ":" in line:
            continue
        if any(ign in lower.split() for ign in ignore_words):
            continue
        # Check digit count (names should not have numbers)
        digit_count = sum(c.isdigit() for c in line)
        if digit_count > 1:
            continue

        # Split into tokens
        words = [w.strip(".,;:|") for w in line.split() if w.strip(".,;:|")]
        if 2 <= len(words) <= 4:
            # Check capitalization
            if all(w[0].isupper() for w in words if len(w) > 0 and w.isalpha()):
                candidate_name = " ".join(words)
                if 4 <= len(candidate_name) <= 45:
                    return (candidate_name, 0.85, "heuristic")

    # If first line alone is 2 capitalized words
    if lines:
        first = lines[0].strip()
        words = first.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
            return (" ".join(words), 0.75, "heuristic")

    return (None, 0.0, "heuristic")


# ── 2. Email Heuristic Extraction ────────────────────────────────────────────

def extract_emails_regex(text: str) -> Tuple[Optional[str], List[str], float, str]:
    """
    Finds all unique email addresses in text.
    Returns: (primary_email, secondary_emails, confidence, source)
    """
    found = EMAIL_REGEX.findall(text)
    if not found:
        return (None, [], 0.0, "regex")

    # Deduplicate while preserving order
    seen: Set[str] = set()
    unique_emails: List[str] = []
    for em in found:
        clean = em.lower().strip()
        if clean not in seen:
            seen.add(clean)
            unique_emails.append(clean)

    primary = unique_emails[0]
    secondaries = unique_emails[1:]
    return (primary, secondaries, 0.99, "regex")


# ── 3. Phone Heuristic Extraction ────────────────────────────────────────────

def extract_phones_regex(text: str) -> Tuple[Optional[str], List[str], float, str]:
    """
    Finds phone numbers in text.
    Returns: (primary_phone, secondary_phones, confidence, source)
    """
    found = PHONE_REGEX.findall(text)
    valid_phones: List[str] = []
    seen: Set[str] = set()

    for p in found:
        raw = p.strip()
        digits = re.sub(r"\D", "", raw)
        if 8 <= len(digits) <= 15:
            if digits not in seen:
                seen.add(digits)
                valid_phones.append(raw)

    if not valid_phones:
        return (None, [], 0.0, "regex")

    return (valid_phones[0], valid_phones[1:], 0.95, "regex")


# ── 4. URLs Heuristic Extraction ─────────────────────────────────────────────

def extract_urls_regex(text: str) -> Dict[str, Tuple[Optional[str], float, str]]:
    """Extract LinkedIn, GitHub, Kaggle, Portfolio, and other links."""
    results: Dict[str, Tuple[Optional[str], float, str]] = {}

    gh = GITHUB_REGEX.search(text)
    results["github_url"] = (_normalize_url(gh.group(0)), 0.95, "regex") if gh else (None, 0.0, "regex")

    li = LINKEDIN_REGEX.search(text)
    results["linkedin_url"] = (_normalize_url(li.group(0)), 0.95, "regex") if li else (None, 0.0, "regex")

    kg = KAGGLE_REGEX.search(text)
    results["kaggle_url"] = (_normalize_url(kg.group(0)), 0.95, "regex") if kg else (None, 0.0, "regex")

    all_urls = GENERIC_URL_REGEX.findall(text)
    other_urls: List[str] = []
    portfolio_cand: Optional[str] = None

    for raw_u in all_urls:
        norm_u = _normalize_url(raw_u)
        lower_u = norm_u.lower()
        if any(ign in lower_u for ign in ["github.com", "linkedin.com", "kaggle.com", "google.com", "w3.org", "schema.org"]):
            continue
        if any(ext in lower_u for ext in [".dev", ".me", ".io", ".app", "portfolio", "personal", "github.io"]):
            if not portfolio_cand:
                portfolio_cand = norm_u
                continue
        other_urls.append(norm_u)

    results["portfolio_url"] = (portfolio_cand, 0.85, "regex") if portfolio_cand else (None, 0.0, "regex")
    results["other_links"] = (",".join(other_urls) if other_urls else None, 0.80, "regex")
    return results


# ── 5. Experience, Skills, Title & Education Heuristics ──────────────────────

def extract_years_experience_heuristic(text: str) -> Tuple[Optional[float], float, str]:
    """Extract years of experience from text (e.g. '5+ years of experience')."""
    match = YEARS_EXP_REGEX.search(text)
    if match:
        try:
            val = float(match.group(1))
            return (val, 0.85, "heuristic")
        except ValueError:
            pass

    # Heuristic: search for year spans like 2018 - 2024 or 2019 - Present
    year_spans = re.findall(r"\b(20\d{2}|19\d{2})\s*(?:-|–|to)\s*(20\d{2}|present|current)\b", text, re.IGNORECASE)
    if year_spans:
        try:
            earliest_year = min(int(s[0]) for s in year_spans if 1980 <= int(s[0]) <= datetime.now().year)
            curr_year = datetime.now().year
            diff = float(max(1, curr_year - earliest_year))
            return (diff, 0.70, "heuristic")
        except Exception:
            pass

    return (None, 0.0, "heuristic")


def extract_skills_heuristic(text: str) -> Tuple[List[str], float, str]:
    """Match words against standard skill lexicon."""
    found: List[str] = []
    seen: Set[str] = set()

    for skill in STANDARD_SKILLS:
        # Match as whole word case-insensitively
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            norm = skill
            if norm.lower() not in seen:
                seen.add(norm.lower())
                found.append(norm)

    if found:
        return (found[:20], 0.85, "heuristic")
    return ([], 0.0, "heuristic")


def extract_current_title_heuristic(text: str, candidate_name: Optional[str] = None) -> Tuple[Optional[str], float, str]:
    """Extract candidate current job title from top section of CV."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # First check lines 1 to 4 for known title keywords
    for line in lines[:5]:
        if candidate_name and line.lower() == candidate_name.lower():
            continue
        for title in TITLE_KEYWORDS:
            if re.search(r"\b" + re.escape(title) + r"\b", line, re.IGNORECASE):
                return (title, 0.85, "heuristic")

    # Generic pattern matching
    title_pattern = re.compile(
        r"\b(?:Senior|Junior|Lead|Principal|Staff|Chief|Head of)?\s*(?:Software|Frontend|Backend|Full[\s-]Stack|DevOps|Data|Cloud|Product|QA|Mobile)\s+(?:Engineer|Developer|Architect|Manager|Lead|Specialist|Scientist|Consultant)\b",
        re.IGNORECASE,
    )
    for line in lines[:6]:
        if candidate_name and line.lower() == candidate_name.lower():
            continue
        match = title_pattern.search(line)
        if match:
            return (match.group(0).strip(), 0.80, "heuristic")

    return (None, 0.0, "heuristic")


def extract_education_heuristic(text: str) -> Tuple[Optional[str], float, str]:
    """Detect degree or education information."""
    match = EDUCATION_DEGREE_REGEX.search(text)
    if match:
        degree = match.group(0).strip()
        # Look around for major / field of study
        return (degree, 0.80, "heuristic")

    # Look for University / College mention
    uni_match = re.search(r"\b(?:University|College|Institute|Polytechnic)\s+of\s+[A-Za-z\s]+|\b[A-Za-z\s]+\s+(?:University|College|Institute)\b", text)
    if uni_match:
        return (uni_match.group(0).strip(), 0.70, "heuristic")

    return (None, 0.0, "heuristic")


def extract_address_heuristic(text: str) -> Tuple[Optional[str], float, str]:
    """Extract city, state/country or mailing location."""
    # Pattern: City, State/Country (e.g., San Francisco, CA or London, UK or Lahore, Pakistan)
    loc_match = re.search(
        r"\b([A-Z][a-zA-Z\s]{2,20}),\s*([A-Z]{2}|[A-Z][a-zA-Z\s]{2,20})(?:\s*,\s*([A-Z][a-zA-Z\s]{2,20}))?\b",
        text[:1500]
    )
    if loc_match:
        cand = loc_match.group(0).strip()
        # Exclude common false positives
        if not any(f in cand.lower() for f in ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "skills", "experience"]):
            return (cand, 0.75, "heuristic")
    return (None, 0.0, "heuristic")


def extract_regex_fields(text: str) -> Dict[str, Tuple[Optional[str], float, str]]:
    """Helper for regex extraction tests and deterministic field verification."""
    email_val, _, email_conf, email_src = extract_emails_regex(text)
    phone_val, _, phone_conf, phone_src = extract_phones_regex(text)
    urls = extract_urls_regex(text)
    return {
        "email": (email_val, email_conf, email_src),
        "phone": (phone_val, phone_conf, phone_src),
        "github_url": urls.get("github_url", (None, 0.0, "regex")),
        "linkedin_url": urls.get("linkedin_url", (None, 0.0, "regex")),
        "kaggle_url": urls.get("kaggle_url", (None, 0.0, "regex")),
        "portfolio_url": urls.get("portfolio_url", (None, 0.0, "regex")),
    }


# ── 6. Deterministic Heuristic + LLM Gap Pipeline ────────────────────────────

def extract_all_deterministic_fields(cv_text: str) -> Dict[str, Any]:
    """
    Runs all regex and heuristic extractors deterministically.
    Never invents values; leaves null if absent.
    """
    name_val, name_conf, name_src = extract_name_heuristic(cv_text)
    email_val, secondaries_em, email_conf, email_src = extract_emails_regex(cv_text)
    phone_val, secondaries_ph, phone_conf, phone_src = extract_phones_regex(cv_text)
    urls = extract_urls_regex(cv_text)
    title_val, title_conf, title_src = extract_current_title_heuristic(cv_text, name_val)
    exp_val, exp_conf, exp_src = extract_years_experience_heuristic(cv_text)
    skills_val, skills_conf, skills_src = extract_skills_heuristic(cv_text)
    edu_val, edu_conf, edu_src = extract_education_heuristic(cv_text)
    addr_val, addr_conf, addr_src = extract_address_heuristic(cv_text)

    other_links_list: List[str] = []
    if urls.get("other_links", (None,))[0]:
        other_links_list = [u for u in urls["other_links"][0].split(",") if u]

    field_metadata: Dict[str, ExtractedFieldMeta] = {
        "name": ExtractedFieldMeta(value=name_val, confidence=name_conf, source=name_src),
        "email": ExtractedFieldMeta(value=email_val, confidence=email_conf, source=email_src),
        "phone": ExtractedFieldMeta(value=phone_val, confidence=phone_conf, source=phone_src),
        "address": ExtractedFieldMeta(value=addr_val, confidence=addr_conf, source=addr_src),
        "current_title": ExtractedFieldMeta(value=title_val, confidence=title_conf, source=title_src),
        "years_of_experience": ExtractedFieldMeta(value=str(exp_val) if exp_val is not None else None, confidence=exp_conf, source=exp_src),
        "top_skills": ExtractedFieldMeta(value=", ".join(skills_val) if skills_val else None, confidence=skills_conf, source=skills_src),
        "education": ExtractedFieldMeta(value=edu_val, confidence=edu_conf, source=edu_src),
        "github_url": ExtractedFieldMeta(value=urls["github_url"][0], confidence=urls["github_url"][1], source=urls["github_url"][2]),
        "linkedin_url": ExtractedFieldMeta(value=urls["linkedin_url"][0], confidence=urls["linkedin_url"][1], source=urls["linkedin_url"][2]),
        "kaggle_url": ExtractedFieldMeta(value=urls["kaggle_url"][0], confidence=urls["kaggle_url"][1], source=urls["kaggle_url"][2]),
        "portfolio_url": ExtractedFieldMeta(value=urls["portfolio_url"][0], confidence=urls["portfolio_url"][1], source=urls["portfolio_url"][2]),
    }

    extracted_data = ExtractedCandidateData(
        name=name_val,
        email=email_val,
        secondary_emails=secondaries_em,
        phone=phone_val,
        secondary_phones=secondaries_ph,
        address=addr_val,
        current_title=title_val,
        years_of_experience=exp_val,
        top_skills=skills_val,
        education=edu_val,
        github_url=urls["github_url"][0],
        linkedin_url=urls["linkedin_url"][0],
        kaggle_url=urls["kaggle_url"][0],
        portfolio_url=urls["portfolio_url"][0],
        other_links=other_links_list,
    )

    return {
        "extracted_data": extracted_data,
        "field_metadata": field_metadata,
    }


async def verify_url_resolves(url: str, timeout_seconds: float = 3.0) -> bool:
    """Check if a URL resolves via an HTTP HEAD/GET probe."""
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=True) as client:
            resp = await client.head(url)
            return resp.status_code < 400
    except Exception:
        return False


async def extract_llm_gaps(
    cv_text: str,
    deterministic: Dict[str, Any],
) -> None:
    """
    Calls OpenRouter LLM only to fill missing gaps and structure information.
    Does not overwrite high-confidence regex/heuristic fields.
    If LLM fails or is rate-limited, safely ignores without breaking.
    """
    extracted_data: ExtractedCandidateData = deterministic["extracted_data"]
    meta: Dict[str, ExtractedFieldMeta] = deterministic["field_metadata"]

    # Check if critical gaps exist
    needs_llm = (
        extracted_data.name is None
        or extracted_data.current_title is None
        or extracted_data.years_of_experience is None
        or len(extracted_data.top_skills) < 3
        or extracted_data.education is None
        or extracted_data.address is None
    )

    if not needs_llm or not cv_text.strip():
        return

    system_instruction = (
        "You are an expert resume parsing engine.\n"
        "Extract candidate details from the provided CV text into a single JSON object.\n"
        "STRICT RULES:\n"
        "- NEVER invent or guess data. If a field is not present in the CV text, return null or empty array.\n"
        "- Extract only what is explicitly stated.\n"
        "- Do not return markdown fences or explanation. Return JSON only."
    )

    user_prompt = (
        f"--- CANDIDATE CV TEXT ---\n{cv_text[:4000]}\n\n"
        "Extract the following fields into JSON:\n"
        "{\n"
        '  "name": string or null,\n'
        '  "email": string or null,\n'
        '  "phone": string or null,\n'
        '  "address": string or null,\n'
        '  "current_title": string or null,\n'
        '  "years_of_experience": number or null,\n'
        '  "top_skills": [string],\n'
        '  "education": string or null,\n'
        '  "github": string or null,\n'
        '  "kaggle": string or null,\n'
        '  "linkedin": string or null,\n'
        '  "portfolio": string or null,\n'
        '  "other_links": [string]\n'
        "}"
    )

    try:
        validated, _, _ = await ai_router.complete_with_chain(
            task_name="extraction",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
            validation_schema=CandidateExtractionLLMOutput,
        )

        # Merge gaps into extracted_data and update metadata
        if not extracted_data.name and validated.name:
            extracted_data.name = validated.name.strip()
            meta["name"] = ExtractedFieldMeta(value=extracted_data.name, confidence=0.85, source="llm")

        if not extracted_data.email and validated.email:
            clean_em = validated.email.strip().lower()
            if "@" in clean_em:
                extracted_data.email = clean_em
                meta["email"] = ExtractedFieldMeta(value=clean_em, confidence=0.85, source="llm")

        if not extracted_data.phone and validated.phone:
            extracted_data.phone = validated.phone.strip()
            meta["phone"] = ExtractedFieldMeta(value=extracted_data.phone, confidence=0.85, source="llm")

        if not extracted_data.address and validated.address:
            extracted_data.address = validated.address.strip()
            meta["address"] = ExtractedFieldMeta(value=extracted_data.address, confidence=0.85, source="llm")

        if not extracted_data.current_title and validated.current_title:
            extracted_data.current_title = validated.current_title.strip()
            meta["current_title"] = ExtractedFieldMeta(value=extracted_data.current_title, confidence=0.85, source="llm")

        if extracted_data.years_of_experience is None and validated.years_of_experience is not None:
            extracted_data.years_of_experience = float(validated.years_of_experience)
            meta["years_of_experience"] = ExtractedFieldMeta(value=str(extracted_data.years_of_experience), confidence=0.85, source="llm")

        if not extracted_data.education and validated.education:
            extracted_data.education = validated.education.strip()
            meta["education"] = ExtractedFieldMeta(value=extracted_data.education, confidence=0.85, source="llm")

        if len(extracted_data.top_skills) < 3 and validated.top_skills:
            for s in validated.top_skills:
                cleaned_s = s.strip()
                if cleaned_s and cleaned_s.lower() not in {sk.lower() for sk in extracted_data.top_skills}:
                    extracted_data.top_skills.append(cleaned_s)
            meta["top_skills"] = ExtractedFieldMeta(value=", ".join(extracted_data.top_skills), confidence=0.85, source="llm")

        if not extracted_data.github_url and validated.github:
            extracted_data.github_url = _normalize_url(validated.github)
            meta["github_url"] = ExtractedFieldMeta(value=extracted_data.github_url, confidence=0.85, source="llm")

        if not extracted_data.linkedin_url and validated.linkedin:
            extracted_data.linkedin_url = _normalize_url(validated.linkedin)
            meta["linkedin_url"] = ExtractedFieldMeta(value=extracted_data.linkedin_url, confidence=0.85, source="llm")

        if not extracted_data.kaggle_url and validated.kaggle:
            extracted_data.kaggle_url = _normalize_url(validated.kaggle)
            meta["kaggle_url"] = ExtractedFieldMeta(value=extracted_data.kaggle_url, confidence=0.85, source="llm")

        if not extracted_data.portfolio_url and validated.portfolio:
            extracted_data.portfolio_url = _normalize_url(validated.portfolio)
            meta["portfolio_url"] = ExtractedFieldMeta(value=extracted_data.portfolio_url, confidence=0.85, source="llm")

        if validated.other_links:
            for ol in validated.other_links:
                norm = _normalize_url(ol)
                if norm not in extracted_data.other_links:
                    extracted_data.other_links.append(norm)

    except Exception as exc:
        logger.info("OpenRouter LLM gap extraction skipped or unavailable (%s). Falling back to regex/heuristics.", exc)


# ── 7. Duplicate Candidate Detection ─────────────────────────────────────────

def check_duplicate_candidate(
    session: Session,
    user_id: uuid.UUID,
    opening_id: uuid.UUID,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> CandidateDuplicateInfo:
    """
    Detects duplicates across the recruiter's candidates in the database
    by email or phone number.
    """
    dup_info = CandidateDuplicateInfo()

    if not email and not phone:
        return dup_info

    # 1. Check duplicate by email
    if email:
        clean_email = email.strip().lower()
        query = select(Candidate).where(
            Candidate.user_id == user_id,
            Candidate.email == clean_email,
        )
        existing = session.exec(query).first()
        if existing:
            opening = session.exec(select(JobOpening).where(JobOpening.id == existing.opening_id)).first()
            dup_info.is_duplicate = True
            dup_info.matched_by = "email"
            dup_info.existing_candidate_id = str(existing.id)
            dup_info.existing_candidate_name = existing.name
            dup_info.existing_candidate_email = existing.email
            dup_info.existing_opening_id = str(existing.opening_id)
            dup_info.existing_opening_title = opening.title if opening else "Unknown"
            dup_info.existing_stage = existing.stage.value if hasattr(existing.stage, "value") else str(existing.stage)
            dup_info.existing_score = existing.score
            return dup_info

    # 2. Check duplicate by phone
    if phone:
        clean_phone = re.sub(r"\D", "", phone)
        if len(clean_phone) >= 8:
            candidates = session.exec(select(Candidate).where(Candidate.user_id == user_id)).all()
            for cand in candidates:
                if cand.phone:
                    cand_digits = re.sub(r"\D", "", cand.phone)
                    if cand_digits and (clean_phone in cand_digits or cand_digits in clean_phone):
                        opening = session.exec(select(JobOpening).where(JobOpening.id == cand.opening_id)).first()
                        dup_info.is_duplicate = True
                        dup_info.matched_by = "phone"
                        dup_info.existing_candidate_id = str(cand.id)
                        dup_info.existing_candidate_name = cand.name
                        dup_info.existing_candidate_email = cand.email
                        dup_info.existing_opening_id = str(cand.opening_id)
                        dup_info.existing_opening_title = opening.title if opening else "Unknown"
                        dup_info.existing_stage = cand.stage.value if hasattr(cand.stage, "value") else str(cand.stage)
                        dup_info.existing_score = cand.score
                        return dup_info

    return dup_info


# ── 8. Extractor Service Class ───────────────────────────────────────────────

class ExtractorService:
    async def preview_and_extract_candidate(
        self,
        session: Session,
        user_id: uuid.UUID,
        opening_id: uuid.UUID,
        cv_text: str,
        file_name: Optional[str] = None,
        file_url: Optional[str] = None,
    ) -> CandidateExtractionPreviewResponse:
        """
        Runs the full extraction pipeline:
        1. Deterministic Regex + Heuristics
        2. LLM Gap-Filling (gracefully skipped if rate limited)
        3. Real DB Duplicate Detection
        4. Confidence Flagging (low confidence or missing fields flagged in amber)
        """
        # Step 1: Run deterministic regex + heuristics
        result = extract_all_deterministic_fields(cv_text)

        # Step 2: Fill gaps using LLM
        await extract_llm_gaps(cv_text, result)

        extracted_data: ExtractedCandidateData = result["extracted_data"]
        field_meta: Dict[str, ExtractedFieldMeta] = result["field_metadata"]

        # Step 3: Check database for duplicates
        duplicate_info = check_duplicate_candidate(
            session=session,
            user_id=user_id,
            opening_id=opening_id,
            email=extracted_data.email,
            phone=extracted_data.phone,
        )

        # Step 4: Identify missing and low-confidence fields for amber UI badges
        missing_fields: List[str] = []
        low_confidence_fields: List[str] = []

        if not extracted_data.name:
            missing_fields.append("name")
        elif field_meta.get("name") and field_meta["name"].confidence < 0.7:
            low_confidence_fields.append("name")

        if not extracted_data.email:
            missing_fields.append("email")
        elif field_meta.get("email") and field_meta["email"].confidence < 0.7:
            low_confidence_fields.append("email")

        if not extracted_data.phone:
            missing_fields.append("phone")
        elif field_meta.get("phone") and field_meta["phone"].confidence < 0.7:
            low_confidence_fields.append("phone")

        if not extracted_data.current_title:
            missing_fields.append("current_title")
        if not extracted_data.top_skills:
            missing_fields.append("top_skills")

        return CandidateExtractionPreviewResponse(
            file_name=file_name,
            file_url=file_url,
            cv_text=cv_text,
            opening_id=str(opening_id),
            extracted_data=extracted_data,
            field_metadata=field_meta,
            duplicate_info=duplicate_info,
            low_confidence_fields=low_confidence_fields,
            missing_fields=missing_fields,
        )

    async def extract_candidate_details(
        self,
        session: Session,
        candidate_id: uuid.UUID,
        user_id: uuid.UUID,
        verify_urls: bool = True,
    ) -> CandidateExtractedDetails:
        """Backwards compatible endpoint method for candidate drawer."""
        candidate = session.exec(
            select(Candidate).where(
                Candidate.id == candidate_id,
                Candidate.user_id == user_id,
            )
        ).first()

        if not candidate:
            raise ValueError(f"Candidate '{candidate_id}' not found.")

        cv_text = candidate.cv_text or ""
        preview = await self.preview_and_extract_candidate(
            session=session,
            user_id=user_id,
            opening_id=candidate.opening_id,
            cv_text=cv_text,
            file_name=candidate.cv_file_url,
        )

        # Update candidate fields
        cand_data = preview.extracted_data
        if not candidate.phone and cand_data.phone:
            candidate.phone = cand_data.phone
        if not candidate.address and cand_data.address:
            candidate.address = cand_data.address
        if not candidate.github_url and cand_data.github_url:
            candidate.github_url = cand_data.github_url
        if not candidate.linkedin_url and cand_data.linkedin_url:
            candidate.linkedin_url = cand_data.linkedin_url
        if not candidate.kaggle_url and cand_data.kaggle_url:
            candidate.kaggle_url = cand_data.kaggle_url
        if not candidate.portfolio_url and cand_data.portfolio_url:
            candidate.portfolio_url = cand_data.portfolio_url

        candidate.extracted_data = cand_data.model_dump()
        session.add(candidate)

        # Sync candidate_links in database & verify URLs
        verified_map: Dict[str, Any] = {}
        for l_type, l_url in [
            ("github", candidate.github_url),
            ("linkedin", candidate.linkedin_url),
            ("portfolio", candidate.portfolio_url),
            ("kaggle", candidate.kaggle_url),
        ]:
            if l_url:
                is_ok = await verify_url_resolves(l_url) if verify_urls else None
                verified_map[l_url] = is_ok
                existing_link = session.exec(
                    select(CandidateLink).where(
                        CandidateLink.candidate_id == candidate.id,
                        CandidateLink.link_type == l_type,
                    )
                ).first()
                if not existing_link:
                    session.add(
                        CandidateLink(
                            candidate_id=candidate.id,
                            user_id=user_id,
                            link_type=l_type,
                            url=l_url,
                            is_verified=is_ok,
                        )
                    )
                else:
                    existing_link.is_verified = is_ok
                    session.add(existing_link)

        session.commit()
        session.refresh(candidate)

        return CandidateExtractedDetails(
            candidate_id=str(candidate.id),
            name=candidate.name,
            email=candidate.email,
            phone=candidate.phone,
            address=candidate.address,
            github_url=candidate.github_url,
            linkedin_url=candidate.linkedin_url,
            portfolio_url=candidate.portfolio_url,
            kaggle_url=candidate.kaggle_url,
            other_links=cand_data.other_links,
            field_metadata=preview.field_metadata,
            links_verified=verified_map,
        )


extractor_service = ExtractorService()
