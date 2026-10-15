import asyncio
import json
import re
import logging
import hashlib
import os
import httpx
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

# Groq Models for Ultra-Fast Inference (<300ms)
GROQ_MODELS = ("openai/gpt-oss-20b", "qwen/qwen3.8-27b")

# Use concrete model IDs instead of `*-latest` aliases for Gemini fallback
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

def generate_with_groq(prompt: str, json_mode: bool = False, system_prompt: Optional[str] = None) -> Optional[str]:
    """Synchronous Groq call for sub-second inference."""
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    elif json_mode:
        messages.append({"role": "system", "content": "You are an expert technical evaluator. Respond ONLY in valid, parseable JSON."})
    messages.append({"role": "user", "content": prompt})

    for model in GROQ_MODELS:
        try:
            payload: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": 0.1,
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}

            with httpx.Client(timeout=7.0) as client:
                resp = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        if content:
                            return content.strip()
                elif resp.status_code == 429:
                    logger.warning(f"Groq 429 rate limit on model {model}")
                    continue
        except Exception as e:
            logger.debug(f"Groq sync call error on {model}: {e}")
            continue
    return None

async def async_generate_with_groq(prompt: str, json_mode: bool = False, system_prompt: Optional[str] = None) -> Optional[str]:
    """Non-blocking async Groq call for high-concurrency parallel evaluation."""
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    elif json_mode:
        messages.append({"role": "system", "content": "You are an expert technical evaluator. Respond ONLY in valid, parseable JSON."})
    messages.append({"role": "user", "content": prompt})

    async with httpx.AsyncClient(timeout=8.0) as client:
        for model in GROQ_MODELS:
            try:
                payload: Dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.1,
                }
                if json_mode:
                    payload["response_format"] = {"type": "json_object"}

                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        if content:
                            return content.strip()
                elif resp.status_code == 429:
                    logger.warning(f"Async Groq 429 rate limit on model {model}")
                    continue
            except Exception as e:
                logger.debug(f"Async Groq error on {model}: {e}")
                continue
    return None

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
    Tier 1: Try ultra-fast Groq inference (<300ms).
    Tier 2: Try Gemini models with cooldown rotation.
    Tier 3: Return None to activate local heuristic engine.
    """
    # 1. Groq ultra-fast attempt
    groq_res = generate_with_groq(prompt)
    if groq_res:
        return groq_res

    # 2. Gemini fallback
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
- Target Experience: Exactly 2.0 Years (Early Career / SDE 1 / Junior-to-Mid Backend Engineer)
- Core Competency: Pure Backend Java Developer (Java 17, Spring Boot, Microservices, REST APIs, PostgreSQL, Docker).

Strict Rejection Criteria (If ANY of these apply, MUST set is_eligible = false):
1. EXPERIENCE OVERQUALIFIED / SENIOR BRACKET:
   - REJECT if minimum required experience is > 2.5 years (e.g. '3+ yrs', '4+ yrs', '5+ yrs', '6+ yrs', '7+ yrs', '8+ yrs', 'minimum 3 years').
   - REJECT if wide senior experience range (e.g. '2-5 yrs', '2-6 yrs', '2-8 yrs', '3-5 yrs', '4-8 yrs', '5-10 yrs').
   - ELIGIBLE ONLY IF tight early career bracket: '0-2 yrs', '1-2 yrs', '1-3 yrs', '2 yrs', '2+ yrs', '2-3 yrs', '2-4 yrs', '0-3 yrs'.
2. SENIOR DESIGNATION IN TITLE OR DESCRIPTION:
   - MUST REJECT: SDE-2, SDE-3, SDE-4, SDE II, SDE III, SDE IV, Software Engineer II, Software Engineer 2, Software Engineer 3, Software Engineer IV, Senior, Lead, Principal, Staff, Architect, Specialist, Consultant, Manager, VP, Director.
3. NON-BACKEND / ROLE DRIFT:
   - MUST REJECT: Fullstack (React/Angular/Vue/HTML/CSS), Frontend, SDET, QA, Automation Tester, Manual Testing, Data Engineer, Big Data, DevOps, SRE, Support Engineer.
4. CONTRACT / TEMPORARY / WALK-IN:
   - MUST REJECT: Contract-to-hire (C2H), 3rd party contract, Freelance, Physical Walk-in drives.
5. NON-TECH FACTORY OR OVERSEAS:
   - MUST REJECT: Non-tech agro/manufacturing factory roles (e.g. Saatvik Agro, Morena MP). Must be in India tech hubs (Bengaluru, Pune, Hyderabad, Gurgaon, Noida, NCR) or Remote.

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
  "ats_score": integer between 50 and 98,
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
    """
    High-performance async evaluation:
    1. Checks in-memory LRU cache (0ms).
    2. Runs async Groq with json_mode (<300ms).
    3. Falls back to thread-pooled Gemini / heuristics if Groq fails or unavailable.
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
- Target Experience: Exactly 2.0 Years (Early Career / SDE 1 / Junior-to-Mid Backend Engineer)
- Core Competency: Pure Backend Java Developer (Java 17, Spring Boot, Microservices, REST APIs, PostgreSQL, Docker).

Strict Rejection Criteria (If ANY of these apply, MUST set is_eligible = false):
1. EXPERIENCE OVERQUALIFIED / SENIOR BRACKET:
   - REJECT if minimum required experience is > 2.5 years (e.g. '3+ yrs', '4+ yrs', '5+ yrs', '6+ yrs', '7+ yrs', '8+ yrs', 'minimum 3 years').
   - REJECT if wide senior experience range (e.g. '2-5 yrs', '2-6 yrs', '2-8 yrs', '3-5 yrs', '4-8 yrs', '5-10 yrs').
   - ELIGIBLE ONLY IF tight early career bracket: '0-2 yrs', '1-2 yrs', '1-3 yrs', '2 yrs', '2+ yrs', '2-3 yrs', '2-4 yrs', '0-3 yrs'.
2. SENIOR DESIGNATION IN TITLE OR DESCRIPTION:
   - MUST REJECT: SDE-2, SDE-3, SDE-4, SDE II, SDE III, SDE IV, Software Engineer II, Software Engineer 2, Software Engineer 3, Software Engineer IV, Senior, Lead, Principal, Staff, Architect, Specialist, Consultant, Manager, VP, Director.
3. NON-BACKEND / ROLE DRIFT:
   - MUST REJECT: Fullstack (React/Angular/Vue/HTML/CSS), Frontend, SDET, QA, Automation Tester, Manual Testing, Data Engineer, Big Data, DevOps, SRE, Support Engineer.
4. CONTRACT / TEMPORARY / WALK-IN:
   - MUST REJECT: Contract-to-hire (C2H), 3rd party contract, Freelance, Physical Walk-in drives.
5. NON-TECH FACTORY OR OVERSEAS:
   - MUST REJECT: Non-tech agro/manufacturing factory roles (e.g. Saatvik Agro, Morena MP). Must be in India tech hubs (Bengaluru, Pune, Hyderabad, Gurgaon, Noida, NCR) or Remote.

Job Posting:
Title: {title}
Description: {description[:8000]}

Respond ONLY with valid JSON:
{{
  "is_eligible": true or false,
  "min_exp": float or null,
  "max_exp": float or null,
  "is_backend_only": true or false,
  "rejection_reason": "null or brief reason why candidate is not eligible",
  "ats_score": integer between 50 and 98,
  "hr_email": "string email or null",
  "google_form_or_apply_url": "url or null"
}}
"""
    # 1. Try async Groq for sub-second response
    if settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY"):
        raw_groq = await async_generate_with_groq(prompt, json_mode=True)
        if raw_groq:
            clean = raw_groq.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            try:
                data = json.loads(clean.strip())
                data["ai_verified"] = True
                data["ai_provider"] = "groq"
                return _cache_eligibility_result(cache_key, data)
            except Exception:
                pass

    # 2. Fall back to thread-pooled Gemini / heuristics
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


async def generate_interview_prep_ai(job_title: str, company: str, job_description: str) -> Dict[str, Any]:
    """Generates an AI-powered 1-page interview prep cheat sheet customized for this specific job."""
    prompt = f"""
You are an expert technical interviewer and staff software engineer.
Generate a high-yield, specific Technical Interview Prep Cheat Sheet for a candidate with 2 Years Experience interviewing for the role of '{job_title}' at '{company}'.

Job Description:
{job_description[:7000]}

Respond ONLY in strict valid JSON:
{{
  "job_title": "{job_title}",
  "company": "{company}",
  "top_technical_questions": [
    {{
      "question": "Specific technical question expected from this JD",
      "hint": "Crisp 1-2 sentence core concept/keywords to mention during the answer",
      "category": "Core Java / Spring Boot / Concurrency / Databases / Kafka / System Design"
    }}
  ],
  "architecture_talking_points": [
    "Key architectural design pattern or scalability talking point relevant to this role"
  ],
  "smart_questions_to_ask_interviewer": [
    "High-impact question to ask the engineering team at the end of the round"
  ]
}}
"""
    if settings.GROQ_API_KEY:
        raw = await async_generate_with_groq(prompt, json_mode=True)
        if raw:
            try:
                clean = raw.strip()
                if clean.startswith("```json"): clean = clean[7:]
                if clean.startswith("```"): clean = clean[3:]
                if clean.endswith("```"): clean = clean[:-3]
                parsed = json.loads(clean.strip())
                if parsed.get("top_technical_questions"):
                    return parsed
            except Exception:
                pass

    # High-quality fallback cheat sheet
    return {
        "job_title": job_title,
        "company": company,
        "top_technical_questions": [
            {
                "question": "How does Spring Boot handle dependency injection and circular dependencies internally?",
                "hint": "Uses ApplicationContext with 3-level singleton cache for Setter injection. Constructor circular dependency throws BeanCurrentlyInCreationException; resolve using @Lazy.",
                "category": "Spring Boot"
            },
            {
                "question": "Explain Java memory model (Heap vs Stack, Metaspace) and how Garbage Collection works in Java 17.",
                "hint": "Objects stored in Heap (Eden, Survivor, Tenured), primitive/references in Stack. Java 17 defaults to G1GC with low-pause incremental collection.",
                "category": "Core Java & JVM"
            },
            {
                "question": "How do you optimize slow database queries and prevent N+1 query problem in Spring Data JPA?",
                "hint": "Use JOIN FETCH or @EntityGraph to load relationships eagerly in 1 query instead of N select statements. Add B-Tree composite indexes on filter columns.",
                "category": "Databases & ORM"
            },
            {
                "question": "How do you achieve idempotency in distributed microservices REST APIs?",
                "hint": "Client sends unique Idempotency-Key header. Server checks Redis/DB with unique constraint before processing; returns cached response if key already processed.",
                "category": "System Design"
            },
            {
                "question": "What is consumer lag in Apache Kafka and how do you monitor and resolve it?",
                "hint": "Lag is difference between latest log offset and committed consumer offset. Resolve by increasing partition count, scaling consumer instances, or batch processing.",
                "category": "Kafka & Messaging"
            }
        ],
        "architecture_talking_points": [
            "Resilience4j Circuit Breaker: Protecting upstream services by shedding load when downstream microservices experience timeouts or high error rates.",
            "Cache-Aside with Redis: Combining TTL with random jitter to prevent cache stampedes and minimizing round trips to PostgreSQL.",
            "Database connection pool tuning: Setting HikariCP pool size = (core_count * 2) + effective_spindle_count for optimal throughput."
        ],
        "smart_questions_to_ask_interviewer": [
            f"How does the backend engineering team at {company} balance paying down technical debt vs shipping new features?",
            "What does your CI/CD deployment cadence look like, and how are database schema migrations handled in production?"
        ]
    }

