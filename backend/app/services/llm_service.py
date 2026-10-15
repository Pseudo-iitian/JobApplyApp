import asyncio
import json
import re
import logging
import hashlib
import os
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Use concrete model IDs instead of `*-latest` aliases. The aliases can resolve
# to the same model and therefore the same exhausted quota bucket.
DEFAULT_MODEL_CANDIDATES = (
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
)
MODEL_CANDIDATES = tuple(
    model.strip()
    for model in os.getenv("GEMINI_MODEL_CANDIDATES", ",".join(DEFAULT_MODEL_CANDIDATES)).split(",")
    if model.strip()
)

_initialized_models: Dict[str, Any] = {}
_model_cooldowns: Dict[str, datetime] = {}
_model_state_lock = Lock()
_last_all_models_unavailable_log: Optional[datetime] = None
_MODEL_UNAVAILABLE_COOLDOWN_SECONDS = 6 * 60 * 60
_DEFAULT_QUOTA_COOLDOWN_SECONDS = 15 * 60

if settings.GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        for m_name in MODEL_CANDIDATES:
            try:
                _initialized_models[m_name] = genai.GenerativeModel(m_name)
            except Exception as e:
                logger.warning(f"Could not load model {m_name}: {e}")
        logger.info(f"Gemini models loaded: {list(_initialized_models.keys())}")
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini SDK: {e}")

def _is_quota_error(error_text: str) -> bool:
    lowered = error_text.lower()
    return any(marker in lowered for marker in (
        "429",
        "quota exceeded",
        "quota_exceeded",
        "resource_exhausted",
        "rate_limit_exceeded",
        "rate limit",
    ))


def _is_unavailable_model_error(error_text: str) -> bool:
    lowered = error_text.lower()
    return "404" in lowered or "not found" in lowered or "not supported" in lowered


def _cooldown_seconds_from_error(error_text: str) -> int:
    match = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", error_text, re.IGNORECASE | re.DOTALL)
    if not match:
        match = re.search(r"retry after\s+(\d+)\s*seconds", error_text, re.IGNORECASE)
    return int(match.group(1)) if match else _DEFAULT_QUOTA_COOLDOWN_SECONDS


def _get_model_cooldown(model_name: str, now: datetime) -> Optional[datetime]:
    with _model_state_lock:
        retry_at = _model_cooldowns.get(model_name)
        if retry_at and retry_at <= now:
            _model_cooldowns.pop(model_name, None)
            return None
        return retry_at


def _pause_model(model_name: str, seconds: int, now: datetime) -> datetime:
    retry_at = now + timedelta(seconds=max(1, seconds))
    with _model_state_lock:
        _model_cooldowns[model_name] = retry_at
    return retry_at


def generate_with_fallback(prompt: str) -> Optional[str]:
    """
    Uses the first available Gemini model and falls back to older, concrete
    versions after a quota or model-availability failure. Quota-exhausted
    models are paused until the API's retry window to prevent request spam.
    """
    global _last_all_models_unavailable_log

    now = datetime.now(timezone.utc)
    attempted_model = False
    for m_name in MODEL_CANDIDATES:
        model = _initialized_models.get(m_name)
        if not model:
            continue

        retry_at = _get_model_cooldown(m_name, now)
        if retry_at:
            continue

        attempted_model = True
        try:
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as exc:
            error_text = str(exc)
            if _is_quota_error(error_text):
                cooldown_seconds = _cooldown_seconds_from_error(error_text)
                retry_at = _pause_model(m_name, cooldown_seconds, now)
                logger.warning(
                    "Gemini quota reached for %s; trying the next lower model. "
                    "This model is paused until %s.",
                    m_name,
                    retry_at.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
                )
                continue
            if _is_unavailable_model_error(error_text):
                retry_at = _pause_model(m_name, _MODEL_UNAVAILABLE_COOLDOWN_SECONDS, now)
                logger.warning(
                    "Gemini model %s is unavailable; trying the next lower model. "
                    "This model is paused until %s.",
                    m_name,
                    retry_at.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
                )
                continue
            logger.warning("Gemini model %s failed: %s. Trying the next candidate...", m_name, exc)

    if not attempted_model:
        with _model_state_lock:
            should_log = (
                _last_all_models_unavailable_log is None
                or now - _last_all_models_unavailable_log >= timedelta(minutes=5)
            )
            if should_log:
                _last_all_models_unavailable_log = now
        if should_log:
            logger.warning("All Gemini models are in cooldown; using the local heuristic fallback.")
    return None

# In-memory LRU cache to achieve sub-millisecond response for repeat requests
_tailor_cache: Dict[str, Dict[str, Any]] = {}
_eligibility_cache: Dict[str, Dict[str, Any]] = {}
_ELIGIBILITY_CACHE_LIMIT = 512


def _cache_eligibility_result(cache_key: str, result: Dict[str, Any]) -> Dict[str, Any]:
    with _model_state_lock:
        if len(_eligibility_cache) >= _ELIGIBILITY_CACHE_LIMIT:
            _eligibility_cache.pop(next(iter(_eligibility_cache)))
        _eligibility_cache[cache_key] = dict(result)
    return result

def extract_job_details_with_llm(job_title: str, description: str, use_llm: bool = False) -> Dict[str, Any]:
    """
    Extracts structured fields from job text:
    - hr_email
    - google_form_url
    - min_experience, max_experience
    - skills_required
    """
    # Baseline regex extraction first (lightning fast < 1ms)
    email_regex = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    found_emails = re.findall(email_regex, description)
    found_emails = [e for e in found_emails if not e.endswith(('.png', '.jpg', '.jpeg', '.svg'))]
    hr_email = found_emails[0] if found_emails else None

    # Google form extraction
    gform_regex = r"(https?://(?:forms\.gle/[a-zA-Z0-9_-]+|docs\.google\.com/forms/[^\s\"'>]+))"
    found_gforms = re.findall(gform_regex, description)
    google_form_url = found_gforms[0] if found_gforms else None

    # Fallback heuristic for experience
    exp_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience", description, re.IGNORECASE)
    min_exp = 2.0
    max_exp = 3.0
    if exp_matches:
        try:
            min_exp = float(exp_matches[0][0])
            if exp_matches[0][1]:
                max_exp = float(exp_matches[0][1])
            else:
                max_exp = min_exp + 1.0
        except Exception:
            pass

    # If explicitly requested and Gemini is available, use it for deep extraction
    if use_llm and _initialized_models:
        prompt = f"""
        Analyze this job posting:
        Job Title: {job_title}
        Description: {description}

        Extract the following as strict JSON:
        {{
            "hr_email": "HR or recruiter email address if mentioned, else null",
            "google_form_url": "Google form or application link if mentioned, else null",
            "min_experience_years": float or null,
            "max_experience_years": float or null,
            "key_skills": ["list", "of", "required", "skills"]
        }}
        """
        raw = generate_with_fallback(prompt)
        if raw:
            try:
                text = raw
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                parsed = json.loads(text.strip())
                return {
                    "hr_email": parsed.get("hr_email") or hr_email,
                    "google_form_url": parsed.get("google_form_url") or google_form_url,
                    "min_experience_years": parsed.get("min_experience_years") or min_exp,
                    "max_experience_years": parsed.get("max_experience_years") or max_exp,
                    "key_skills": parsed.get("key_skills", ["Java", "Spring Boot"])
                }
            except Exception as e:
                logger.warning(f"Error parsing Gemini response: {e}")

    return {
        "hr_email": hr_email,
        "google_form_url": google_form_url,
        "min_experience_years": min_exp,
        "max_experience_years": max_exp,
        "key_skills": ["Java", "Spring Boot", "Microservices", "REST API", "SQL"]
    }

def ai_evaluate_job_eligibility(title: str, description: str) -> Dict[str, Any]:
    """
    Evaluates whether a candidate with 2 YOE (Pure Java Backend) is strictly eligible using Gemini AI:
    - Candidate: Abhishek Verma (2.0 YOE, Pure Backend Java / Spring Boot / Microservices / SQL).
    - Hard Rejection Rules:
      1. Fullstack / Frontend: (React, Angular, Vue, UI/UX, Web frontend) -> REJECT!
      2. Experience: Minimum required experience > 2.0 years (3+, 3-5, 4+, 5+, etc.) -> REJECT!
         (Roles accepting 0-2, 1-2, 1-3, 2-3, 2-4, 2-5, 2+, 2 yrs are ELIGIBLE).
      3. Senior / Leadership: (Senior, Lead, Architect, SDE-2, SDE-3, Manager, Principal) -> REJECT!
      4. Location: Must be in India or Remote. (UK, USA, Europe, Canada, Australia -> REJECT).
    """
    cache_key = hashlib.sha256(f"{title}\n{description}".encode("utf-8")).hexdigest()
    with _model_state_lock:
        cached_result = _eligibility_cache.get(cache_key)
    if cached_result:
        return dict(cached_result)

    prompt = f"""
You are an expert technical recruiter evaluating job matches for a specific candidate.

Candidate Profile:
- Name: Abhishek Verma
- Current Experience: Exactly 2.0 Years
- Core Competency: Pure Backend Java Developer (Java 17, Spring Boot, Microservices, REST APIs, PostgreSQL, Docker).
- Strict Eligibility Constraints:
  1. STRICTLY Pure Backend Java only. ZERO Fullstack roles (if title or description requires Full Stack, Frontend, React, Angular, Vue, HTML/CSS as core requirement -> REJECT).
  2. STRICT 2 YOE Experience Limit: Minimum required experience must be <= 2.0 years.
     - ELIGIBLE: '0-2 yrs', '1-2 yrs', '1-3 yrs', '2 yrs', '2+ yrs', '2-4 yrs', '2-5 yrs' (a 2 YOE candidate qualifies).
     - INELIGIBLE: '3+ yrs', '3-5 yrs', '3 to 6 yrs', '4+ yrs', '5+ yrs', '3-10 yrs', 'minimum 3 years' -> MUST REJECT!
  3. STRICTLY NO Senior / Lead / Architect / SDE-2 / SDE-3 / SDE II / SDE III roles.
  4. Must be India-based or Remote. Rejects overseas/foreign onsite jobs.

Job Posting:
Title: {title}
Description: {description[:10000]}

Respond ONLY with valid JSON:
{{
  "is_eligible": true or false,
  "min_exp": float or null,
  "max_exp": float or null,
  "is_backend_only": true or false,
  "rejection_reason": "null or brief reason why candidate is not eligible",
  "ats_score": integer between 70 and 98,
  "hr_email": "string email or null",
  "google_form_or_apply_url": "url or null"
}}
"""
    raw = generate_with_fallback(prompt)
    if not raw:
        return _cache_eligibility_result(
            cache_key,
            {"is_eligible": True, "ai_verified": False, "rejection_reason": None, "ats_score": 88},
        )

    clean = raw.strip()
    if clean.startswith("```json"):
        clean = clean[7:]
    if clean.startswith("```"):
        clean = clean[3:]
    if clean.endswith("```"):
        clean = clean[:-3]
    try:
        data = json.loads(clean.strip())
        data["ai_verified"] = True
        return _cache_eligibility_result(cache_key, data)
    except Exception as e:
        logger.warning(f"Failed to parse AI evaluation JSON: {e}")
        return _cache_eligibility_result(
            cache_key,
            {"is_eligible": True, "ai_verified": False, "rejection_reason": None, "ats_score": 88},
        )


async def async_ai_evaluate_job_eligibility(title: str, description: str) -> Dict[str, Any]:
    """Non-blocking async wrapper around ai_evaluate_job_eligibility using asyncio.to_thread."""
    return await asyncio.to_thread(ai_evaluate_job_eligibility, title, description)


def tailor_resume_ai(resume_text: str, job_title: str, company: str, job_description: str) -> Dict[str, Any]:
    """
    Tailors resume specifically for this job description using Gemini Flash Lite:
    - Calculates ATS Match Score
    - Highlights Missing Keywords
    - Rewrites Professional Summary
    - Provides ATS Bullet Points for 2 Years Experience
    - Drafts Cover Letter
    - Drafts Personalized Cold Email to HR
    """
    # Cache key for low latency
    cache_key = f"{company}:{job_title}:{hash(resume_text)}:{hash(job_description)}"
    if cache_key in _tailor_cache:
        logger.info("Serving tailored resume from memory cache (0ms latency).")
        return _tailor_cache[cache_key]

    if _initialized_models:
        prompt = f"""
        You are an elite Tech Career Coach & ATS Optimizer.
        The user is a Java Developer with 2 years of experience.

        User's Current Resume Content:
        {resume_text}

        Target Job:
        Title: {job_title}
        Company: {company}
        Job Description:
        {job_description}

        Generate a high-conversion application package as strict JSON:
        {{
            "match_score": integer between 70 and 98,
            "summary_of_match": "2-3 sentences explaining strong alignment with 2 yrs Java/Spring Boot requirements",
            "missing_keywords": ["3-5 important keywords from JD that should be emphasized"],
            "tailored_summary": "Compelling 3-4 sentence professional summary customized for {company}",
            "tailored_experience_bullets": [
                "Engineered scalable Microservices using Java 17 and Spring Boot, reducing API latency by 25%.",
                "Designed and optimized PostgreSQL database queries and Hibernate ORM mappings for high-throughput transactions.",
                "Automated CI/CD pipelines with Docker and Git, ensuring seamless deployment and 99.9% uptime."
            ],
            "tailored_cover_letter": "Professional cover letter highlighting 2 years of Java development experience and passion for {company}.",
            "hr_email_draft": "Subject and concise cold email pitching the 2 years Java developer profile to the hiring team."
        }}
        """
        raw = generate_with_fallback(prompt)
        if raw:
            try:
                text = raw
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                result = json.loads(text.strip())
                _tailor_cache[cache_key] = result
                return result
            except Exception as e:
                logger.warning(f"Error parsing Gemini response: {e}")

    # High quality fallback template
    fallback_result = {
        "match_score": 92,
        "summary_of_match": f"Strong fit for {job_title} at {company}. Your 2 years of experience in Java, Spring Boot, and RESTful Microservices directly align with the core requirements.",
        "missing_keywords": ["Kafka / Messaging", "Kubernetes", "JUnit / Mockito Test Coverage", "Cloud Deployment"],
        "tailored_summary": f"Results-driven Java Developer with 2 years of proven expertise in designing and deploying robust microservices using Java, Spring Boot, and PostgreSQL. Experienced in building high-throughput REST APIs and eager to contribute to {company}'s backend engineering team.",
        "tailored_experience_bullets": [
            f"Spearheaded backend service development with Java and Spring Boot, optimizing response times by 30% for high-concurrency endpoints.",
            f"Designed scalable relational schemas in PostgreSQL, writing complex queries and tuning Hibernate/JPA transactions.",
            f"Implemented RESTful APIs and secure OAuth2/JWT authentication compliant with modern microservices architecture.",
            f"Integrated automated unit and integration tests using JUnit and Mockito, raising code coverage above 85%."
        ],
        "tailored_cover_letter": f"Dear Hiring Team at {company},\n\nI am writing to express my strong enthusiasm for the {job_title} position. With 2 years of hands-on experience in Java, Spring Boot, and microservices architecture, I have contributed to building scalable, production-grade backend applications.\n\nAt my previous role, I focused on clean code, API performance optimization, and PostgreSQL database management. I am excited about {company}'s vision and would welcome the opportunity to discuss how my skill set can support your engineering objectives.\n\nSincerely,\nJava Backend Developer",
        "hr_email_draft": f"Subject: Application: {job_title} - 2 Years Experience (Java / Spring Boot)\n\nHi {company} Hiring Team,\n\nI came across your opening for the {job_title} role and wanted to reach out directly. I bring 2 years of solid backend experience specializing in Java 17, Spring Boot, Microservices, and PostgreSQL.\n\nMy background includes optimizing REST APIs and building reliable distributed services. I have attached my tailored resume for your review and would love to connect for a quick 10-minute introductory conversation.\n\nBest regards,\n[Your Name] | Contact: [Your Phone/Email]"
    }
    _tailor_cache[cache_key] = fallback_result
    return fallback_result
