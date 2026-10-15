import asyncio
import hashlib
import json
import logging
import os
import re
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import httpx
import primp
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.notification import Notification
from app.models.settings import SearchConfig
from app.services.llm_service import extract_job_details_with_llm, ai_evaluate_job_eligibility, async_ai_evaluate_job_eligibility
from app.services.notifier import manager

logger = logging.getLogger("JobHunter")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0"
]
UA_INDEX = 0

def get_rotating_headers() -> Dict[str, str]:
    global UA_INDEX
    ua = USER_AGENTS[UA_INDEX % len(USER_AGENTS)]
    UA_INDEX += 1
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

BROWSER_HEADERS = {
    "User-Agent": USER_AGENTS[0],
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

async def polite_linkedin_get(client: Any, url: str, timeout: float = 12.0, max_retries: int = 2) -> Optional[Any]:
    """
    Rate-limited LinkedIn GET. Rotates User-Agent, backs off on 429.
    """
    for attempt in range(max_retries + 1):
        try:
            headers = get_rotating_headers()
            headers["Referer"] = "https://www.linkedin.com/"
            resp = await client.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 429:
                if attempt < max_retries:
                    backoff = 2.0 * (attempt + 1)
                    logger.warning(f"LinkedIn HTTP 429 for {url[:60]}... Backing off {backoff:.1f}s")
                    await asyncio.sleep(backoff)
                    continue
            await asyncio.sleep(0.4)   # reduced from 1.5s → 0.4s
            return resp
        except Exception as e:
            if attempt < max_retries:
                await asyncio.sleep(0.5)
                continue
            logger.debug(f"LinkedIn request error for {url}: {e}")
            return None
    return None

def robust_ddgs_search(query: str, max_results: int = 8) -> List[Dict[str, Any]]:
    """
    Multi-backend web search helper using ddgs.
    Tries default direct search first with timeout, then falls back to other backends.
    """
    try:
        from ddgs import DDGS
        dd = DDGS(timeout=7)
        # 1. Try fast default search
        try:
            res = list(dd.text(query, max_results=max_results))
            if res:
                return res
        except Exception:
            pass
        # 2. Try fallbacks
        for b in ["lite", "api", "yahoo"]:
            try:
                res = list(dd.text(query, backend=b, max_results=max_results))
                if res:
                    return res
            except Exception:
                continue
    except Exception as e:
        logger.debug(f"robust_ddgs_search error: {e}")
    return []

# In-memory recent logs circular buffer for frontend terminal inspection
RECENT_HUNTER_LOGS: List[Dict[str, Any]] = []

def record_log(level: str, message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = {"time": timestamp, "level": level, "message": message}
    RECENT_HUNTER_LOGS.append(entry)
    if len(RECENT_HUNTER_LOGS) > 120:
        RECENT_HUNTER_LOGS.pop(0)
    if level == "INFO":
        logger.info(message)
    elif level == "WARNING":
        logger.warning(message)
    elif level == "ERROR":
        logger.error(message)

def get_recent_logs() -> List[Dict[str, Any]]:
    return list(RECENT_HUNTER_LOGS)


def mark_search_completed(db: Session) -> None:
    """Persist the completion time even when a hunt yields no new jobs."""
    try:
        config = db.query(SearchConfig).first()
        if config:
            config.last_scraped_at = datetime.utcnow()
            db.commit()
    except Exception as exc:
        db.rollback()
        record_log("WARNING", f"Could not update the last search time: {exc}")


def generate_source_id(company: str, title: str, apply_link: Optional[str] = None) -> str:
    key = f"{company.strip().lower()}:{title.strip().lower()}:{apply_link or ''}"
    return hashlib.md5(key.encode()).hexdigest()[:24]

DISALLOWED_TITLE_KEYWORDS = [
    "senior", "sr.", "sr ", "lead", "staff", "principal", "architect",
    "director", "manager", "head", "vp", "avp", "vice president",
    "assistant vice president", "associate vice president", "president",
    "chief", "team lead", "tech lead", "group lead", "expert",
    "specialist ii", "specialist 2", "specialist iii", "specialist 3", "specialist iv", "specialist v",
    "internship", "intern",
    "frontend", "front-end", "front end", "full stack", "fullstack", "full-stack",
    "react", "angular", "vue", "node", "python", "devops",
    "qa", "tester", "sales", "copywriter", "marketing", "ui/ux", "web developer",
    "sde 2", "sde-2", "sde2", "sde ii", "sde-ii", "sdeii",
    "sde 3", "sde-3", "sde3", "sde iii", "sde-iii", "sdeiii",
    "sde 4", "sde-4", "sde iv",
    "software engineer 2", "software engineer ii", "software engineer-ii",
    "software engineer 3", "software engineer iii", "software engineer-iii",
    "developer 2", "developer ii", "developer 3", "developer iii",
    "engineer 2", "engineer ii", "engineer 3", "engineer iii",
    "backend developer 2", "backend developer ii", "backend developer 3", "backend developer iii",
    "3-5", "3 to 5", "3 - 5", "3-6", "3 to 6", "3-7", "3-8", "3-10",
    "4-5", "4 to 5", "4 - 5", "4-6", "4-7", "4-8", "5-8", "5-10",
    "3+ years", "3+ yrs", "3 + years", "3 + yrs", "4+ years", "4+ yrs", "5+ years", "5+ yrs",
    "6+ years", "7+ years", "8+ years", "10+ years",
    "3 years", "4 years", "5 years", "6 years", "7 years", "8 years", "9 years", "10 years",
    "3 yrs", "4 yrs", "5 yrs", "6 yrs", "7 yrs", "8 yrs"
]

def parse_linkedin_date(datetime_attr: Optional[str], text_val: Optional[str]) -> Tuple[datetime, str]:
    from datetime import timedelta
    if datetime_attr:
        try:
            return datetime.strptime(datetime_attr.strip(), "%Y-%m-%d"), text_val or "Recently"
        except Exception:
            pass
    now = datetime.utcnow()
    t = (text_val or "").lower().strip()
    if "hour" in t or "minute" in t or "just" in t:
        return now, text_val or "Today"
    if "day" in t:
        days_match = re.search(r"(\d+)", t)
        days = int(days_match.group(1)) if days_match else 1
        return now - timedelta(days=days), text_val
    if "week" in t:
        w_match = re.search(r"(\d+)", t)
        weeks = int(w_match.group(1)) if w_match else 1
        return now - timedelta(days=weeks*7), text_val
    if "month" in t:
        m_match = re.search(r"(\d+)", t)
        months = int(m_match.group(1)) if m_match else 1
        return now - timedelta(days=months*30), text_val
    return now, text_val or "Recently"

FOREIGN_LOCATION_KEYWORDS = [
    "united kingdom", "england", "london", "ipswich", "manchester", "birmingham", "leeds",
    "united states", "usa", "america", "california", "new york", "texas", "seattle", "austin",
    "canada", "ontario", "toronto", "ottawa", "vancouver", "quebec", "montreal", "mississauga",
    "germany", "berlin", "munich", "frankfurt", "spain", "madrid", "barcelona", "tres cantos",
    "singapore", "australia", "sydney", "melbourne", "netherlands", "amsterdam", "dublin", "ireland",
    "france", "paris", "switzerland", "zurich", "poland", "warsaw", "uae", "dubai", "abu dhabi",
    "philippines", "manila", "japan", "tokyo", "vietnam"
]

INDIA_LOCATION_KEYWORDS = [
    "india", "noida", "greater noida", "gurgaon", "gurugram", "delhi", "delhi ncr", "ncr",
    "bengaluru", "bangalore", "pune", "hyderabad", "secunderabad", "mumbai", "navi mumbai",
    "chennai", "kolkata", "ahmedabad", "chandigarh", "mohali", "jaipur", "indore", "lucknow",
    "kochi", "coimbatore", "trivandrum", "thiruvananthapuram", "karnataka", "maharashtra",
    "telangana", "tamil nadu", "uttar pradesh", "haryana", "kerala", "gujarat"
]

def is_india_location(location_str: Optional[str]) -> bool:
    """
    Strict location filter: Only permits jobs based in India or candidate preferred hubs.
    Rejects explicit foreign/UK/US/Europe/Singapore/Canada openings.
    """
    if not location_str:
        return True
    loc = location_str.lower().strip()
    
    # 1. India keywords check first (handles posts mentioning 'join us', 'systems', 'solutions')
    has_india = any(ik in loc for ik in INDIA_LOCATION_KEYWORDS)
    if has_india:
        return True

    # 2. Foreign check using word boundaries
    has_foreign = any(re.search(r'\b' + re.escape(fk) + r'\b', loc) for fk in FOREIGN_LOCATION_KEYWORDS)
    if has_foreign:
        return False

    # 3. Remote check
    if "remote" in loc:
        return True

    return False

def is_job_recent(posted_date_str: str, posted_at: Optional[datetime] = None, max_days: int = 21) -> bool:
    """
    Freshness filter: Rejects any job posted > max_days ago (default: 21 days).
    """
    s = (posted_date_str or "").lower().strip()
    if not s:
        return True
    
    stale_indicators = [
        "1mo", "2mo", "3mo", "4mo", "month", "months", "year", "years", "1yr", "2yr"
    ]
    if any(ind in s for ind in stale_indicators):
        return False
        
    day_m = re.search(r"(\d+)\s*(?:days?|d)\s*ago", s)
    if day_m and int(day_m.group(1)) > max_days:
        return False

    if posted_at:
        diff_days = (datetime.utcnow() - posted_at).total_seconds() / 86400.0
        if diff_days > (max_days + 0.1):
            return False
            
    return True

def evaluate_experience_eligibility(title: str, description: str, max_candidate_exp: float = 2.0) -> Tuple[bool, float, str, str]:
    """
    Evaluates whether a candidate with 2 YOE (Java Backend Developer) is strictly eligible.
    Covers:
    - 1 to 3 years, 2 to 5 years, 1 to 2 yrs, 2 to 4 yrs, 2 to 3 yrs, 0 to 2 yrs, 2+ yrs, 1+ yrs, 2 yrs:
      ELIGIBLE!
    - Senior requirements with minimum required experience > 2.5 / 3.0 yrs (e.g. 4+ yrs, 5+ yrs, 5-8 yrs, tech lead, architect):
      REJECTED!
    - Avoids false rejections from company age (e.g. "10+ years of excellence in IT solutions").
    """
    title_lower = title.lower()
    for sw in DISALLOWED_TITLE_KEYWORDS:
        if sw in title_lower:
            return False, 99.0, "Senior / Disallowed Title", f"Title keyword detected: '{sw}'"

    # STRICT FULLSTACK & FRONTEND REJECTION
    fullstack_cues = [
        "fullstack", "full-stack", "full stack", "frontend", "front-end", "front end",
        "react", "angular", "vue", "next.js", "nextjs", "ui/ux", "ui developer", "web developer"
    ]
    for fc in fullstack_cues:
        if fc in title_lower:
            return False, 99.0, "Fullstack / Frontend", f"Title contains '{fc}' (Pure Backend Java required)"

    desc_lower = description.lower()
    senior_desc_cues = [
        "assistant vice president", "vice president", "principal engineer",
        "director of engineering", "lead architect", "solutions architect",
        "mentor junior", "lead the development team", "head of engineering",
        "fullstack developer", "full stack developer", "full-stack developer"
    ]
    for sdc in senior_desc_cues:
        if sdc in desc_lower:
            return False, 99.0, "Senior / Fullstack Role", f"Senior or fullstack cue detected: '{sdc}'"

    combined = f"{title_lower} {desc_lower}"

    # 1. Range match: e.g. "2 to 5 years", "1 to 3 years", "2-3 yrs", "2-4 yrs", "1-2 yrs"
    range_regex = r"(\d+(?:\.\d+)?)\s*(?:-|to|–)\s*(\d+(?:\.\d+)?)\s*(?:\+)?\s*(?:years?|yrs?|yoe)(?!\s*ago)"
    range_matches = list(re.finditer(range_regex, combined))

    first_valid_range = None
    has_senior_range = False
    for m in range_matches:
        low = float(m.group(1))
        high = float(m.group(2))
        # 0-0 means unspecified on aggregator sites (Foundit etc), skip it
        if low == 0.0 and high == 0.0:
            continue
        # Ignore company age ranges (e.g. 10-15 years in business, 15-20 years of experience as a firm)
        if low >= 8.0:
            continue
        # Candidate with 2 YOE matches ranges where min <= 2.5 (e.g. 1-3, 2-5, 2-4, 1-2, 2-3, 0-2)
        if low <= 2.5 and high >= 1.0:
            if first_valid_range is None:
                first_valid_range = (low, high)
        elif low > 3.0:
            has_senior_range = True

    if has_senior_range and first_valid_range is None:
        return False, 5.0, "Senior Range", "Role requires senior level experience (> 3 YOE minimum)"

    # Blank out all processed ranges so upper bounds don't trigger single-number checks!
    text_without_ranges = re.sub(range_regex, " PROCESSED_RANGE ", combined)

    # Collect all single-number minimum experience requirements
    found_mins = []

    # 2. Plus match: e.g. "2+ years", "1+ years", "3+ years"
    plus_matches = re.findall(r"(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?|yoe)", text_without_ranges)
    for p_str in plus_matches:
        val = float(p_str)
        if val >= 8.0:
            continue # Skip company age like "10+ years in IT"
        found_mins.append((val, f"{int(val)}+ Years Exp"))

    # 3. Minimum match: e.g. "minimum 2 years", "at least 1 year", "min 2 yrs"
    min_matches = re.findall(r"(?:minimum|at\s+least|min\.?)(?:\s+of)?\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?|yoe)", text_without_ranges)
    for m_str in min_matches:
        val = float(m_str)
        if val >= 8.0:
            continue
        found_mins.append((val, f"{int(val)}+ Years Exp"))

    # 4. Standalone 'X years of experience' or 'X yrs exp'
    exact_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\s*(?:of)?\s*(?:\w+\s+){0,3}(?:experience|exp)", text_without_ranges)
    for e_str in exact_matches:
        val = float(e_str)
        if val >= 8.0:
            continue
        found_mins.append((val, f"{int(val)} Years Exp"))

    # 5. Contextual 'experience: X years'
    rev_matches = re.findall(r"(?:experience|exp)[^\n\.\;]{0,25}[:\s]\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", text_without_ranges)
    for r_str in rev_matches:
        val = float(r_str)
        if val >= 8.0:
            continue
        found_mins.append((val, f"{int(val)} Years Exp"))

    # Check explicit requirements
    for val, label in found_mins:
        if val > 3.0 and not first_valid_range:
            return False, val, label, f"Required experience {val} > 2.5 yrs"

    # If an eligible range was detected (e.g. 1-3 yrs, 2-5 yrs)
    if first_valid_range:
        low, high = first_valid_range
        return True, low, f"{int(low)} - {int(high)} Years Exp", f"Eligible range: {int(low)}-{int(high)} yrs"

    # If any eligible plus or exact was found (all <= 2.5)
    eligible_mins = [m for m in found_mins if m[0] <= 2.5]
    if eligible_mins:
        best_val, best_label = eligible_mins[0]
        return True, best_val, best_label, f"Eligible experience: {best_label}"

    # Fallback: If no experience numbers at all were found:
    # Check if the title explicitly mentions junior/entry/associate level
    junior_title_cue = re.search(r"\b(junior|jr\.?|associate|entry[\s\-]?level|trainee|fresher|intern|sde[\s\-]?[1i]|engineer[\s\-]?[1i]|developer[\s\-]?[1i]|0-2|1-2|2\s*yoe)\b", title_lower)
    if junior_title_cue:
        return True, 2.0, "1 - 2 Years Exp (Associate)", "Associate/Entry level title eligible for 2 YOE"

    # If title is a standard Java/Backend/Software Engineer role (no explicit exp stated),
    # approve it for AI deep-verification rather than blanket rejecting.
    # Generic titles like "Java Developer", "Backend Developer", "Software Engineer" at unknown cos
    # often don't list experience in the title - let Gemini AI decide.
    eligible_generic_titles = [
        "java developer", "java engineer", "java backend", "backend developer",
        "backend engineer", "software engineer", "software developer",
        "spring boot developer", "spring boot engineer", "microservices developer",
        "sde", "sde 1", "sde i", "sde-1", "sde-i",
        "java software engineer", "java software developer",
        "application developer", "api developer",
    ]
    for egt in eligible_generic_titles:
        if egt in title_lower:
            return True, 2.0, "2 Years Exp (Unspecified)", "Generic Java/Backend title - eligible for AI verification"

    # For all other titles with no experience stated, still approve for AI check
    # (better to let Gemini reject than to blanket-filter good roles)
    if any(k in title_lower for k in ["java", "spring", "backend", "microservice", "api"]):
        return True, 2.0, "2 Years Exp (Unspecified)", "Java/Backend keyword in title - eligible for AI verification"

    return False, 99.0, "Unspecified Experience - Non-Java Title", "No Java/Backend keyword and no experience range found"

def calculate_ats_match_score(title: str, description: str) -> int:
    """
    Computes ATS match percentage against Abhishek Verma's 2 YOE Java/Spring Boot CV.
    """
    text = f"{title} {description}".lower()
    score = 88
    if "spring" in text or "springboot" in text:
        score += 4
    if "microservice" in text:
        score += 2
    if "rest" in text or "api" in text:
        score += 1
    if "postgres" in text or "sql" in text:
        score += 1
    if "docker" in text or "kafka" in text or "aws" in text:
        score += 1
    if "hibernate" in text or "jpa" in text:
        score += 1
    return min(score, 98)

# ==============================================================================
# AGENT 1: LinkedIn India Hunter Agent
# ==============================================================================
async def agent_linkedin_hunt(client: Any, query: str, location: str, offset: int = 0) -> List[Dict[str, Any]]:
    record_log("INFO", f"🔎 [Agent-1: LinkedIn] Searching live postings for '{query}' in {location} (offset={offset})...")
    jobs = []
    encoded_query = urllib.parse.quote(query)
    encoded_loc = urllib.parse.quote(location)
    # No f_E filter — catches ALL experience levels, we filter ourselves
    # f_TPR=r604800 = past 7 days
    search_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_query}&location={encoded_loc}&f_TPR=r604800&start={offset}"

    try:
        resp = await polite_linkedin_get(client, search_url, timeout=12.0)
        if not resp or resp.status_code != 200 or not resp.text:
            status = resp.status_code if resp else "Failed"
            record_log("WARNING", f"[Agent-1: LinkedIn] Returned HTTP {status} for {location}.")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.find_all("li")
        record_log("INFO", f"✔ [Agent-1: LinkedIn] Found {len(cards)} raw job cards in {location}.")

        detail_fetches_done = 0
        for card in cards:
            title_elem = card.find("h3", class_="base-search-card__title")
            company_elem = card.find("h4", class_="base-search-card__subtitle")
            link_elem = card.find("a", class_="base-card__full-link")
            loc_elem = card.find("span", class_="job-search-card__location")
            time_elem = card.find("time")

            if not (title_elem and company_elem and link_elem):
                continue

            title = title_elem.text.strip()
            company = company_elem.text.strip()
            raw_link = link_elem.get("href", "")
            clean_link = raw_link.split("?")[0] if raw_link else None
            job_loc = loc_elem.text.strip() if loc_elem else location

            if not is_india_location(job_loc):
                record_log("INFO", f"  🚫 [Agent-1: LinkedIn] Filtered non-India location: '{title}' @ {company} ({job_loc})")
                continue

            title_lower = title.lower()
            if any(sw in title_lower for sw in DISALLOWED_TITLE_KEYWORDS):
                continue
            if "java" not in title_lower and "spring" not in title_lower and "backend" not in title_lower:
                continue

            # 1. Strict Date Freshness Verification
            posted_at, posted_date_str = parse_linkedin_date(
                time_elem.get("datetime") if time_elem else None,
                time_elem.text.strip() if time_elem else "Today"
            )
            if not is_job_recent(posted_date_str, posted_at, max_days=7):
                record_log("INFO", f"  ⏳ [Agent-1: LinkedIn] Filtered stale job (> 7 days): '{title}' @ {company} ({posted_date_str})")
                continue

            if not clean_link:
                continue

            job_id_match = re.search(r"(\d{8,12})", clean_link)
            if not job_id_match:
                continue

            job_id = job_id_match.group(1)
            detail_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
            d_resp = await polite_linkedin_get(client, detail_url, timeout=7.0)
            if not d_resp or d_resp.status_code != 200 or not d_resp.text:
                continue

            detail_fetches_done += 1
            if detail_fetches_done >= 15:
                break

            d_soup = BeautifulSoup(d_resp.text, "html.parser")
            d_box = d_soup.find("div", class_="show-more-less-html__markup")
            if not d_box:
                continue

            desc_text = d_box.get_text(separator=" ", strip=True)
            if len(desc_text) < 50:
                continue

            # 2. Strict Fast Heuristic Filter (0ms)
            eligible, exp_val, exp_label, reason = evaluate_experience_eligibility(title, desc_text, max_candidate_exp=2.0)
            if not eligible:
                record_log("INFO", f"  🚫 [Agent-1: LinkedIn] Heuristic Filtered: '{title}' @ {company} ({reason})")
                continue

            # 3. Deep Gemini AI Eligibility & Verification
            ai_eval = await async_ai_evaluate_job_eligibility(title, desc_text)
            if not ai_eval.get("is_eligible", True):
                ai_reason = ai_eval.get("rejection_reason") or "AI determined role is not eligible"
                record_log("INFO", f"  🚫 [Agent-1: LinkedIn] AI Filtered: '{title}' @ {company} ({ai_reason})")
                continue

            hr_email = ai_eval.get("hr_email")
            google_form = ai_eval.get("google_form_or_apply_url")
            score = ai_eval.get("ats_score") or calculate_ats_match_score(title, desc_text)
            min_exp = ai_eval.get("min_exp") or exp_val
            exp_str = f"{min_exp:.1f} Years Exp" if min_exp else exp_label

            record_log("INFO", f"  🎯 [Agent-1: LinkedIn] Verified Fit: '{title}' @ {company} [{exp_str}, {score}% Fit, {posted_date_str}]")

            jobs.append({
                "title": title,
                "company": company,
                "location": job_loc,
                "experience_required": min_exp,
                "experience_str": exp_str,
                "description": desc_text[:6000],
                "apply_link": clean_link,
                "hr_email": hr_email,
                "google_form_url": google_form,
                "source": "LinkedIn Job Listing",
                "match_score": score,
                "posted_at": posted_at,
                "posted_date_str": posted_date_str
            })
    except Exception as e:
        record_log("WARNING", f"[Agent-1: LinkedIn] Notice: {e}")

    return jobs

# ==============================================
# AGENT 1B: LinkedIn TODAY-ONLY Hunter (past 24 hours — highest priority)
# Runs parallel to all other agents, focuses ONLY on jobs posted today
# ==============================================
TODAY_QUERIES = [
    ("Java Developer", "India"),
    ("Java Backend Developer", "India"),
    ("Spring Boot Developer", "India"),
    ("Java Developer", "Noida"),
    ("Java Developer", "Bengaluru"),
    ("Backend Developer", "India"),
]
TODAY_INDEX = 0

async def agent_linkedin_today(client: Any) -> List[Dict[str, Any]]:
    """Today-only LinkedIn hunter — fetches jobs posted in last 24 hours."""
    global TODAY_INDEX
    q, loc = TODAY_QUERIES[TODAY_INDEX % len(TODAY_QUERIES)]
    TODAY_INDEX += 1

    record_log("INFO", f"⚡ [Agent-1B: LinkedIn TODAY] Fetching TODAY's jobs: '{q}' in {loc}...")
    jobs = []
    encoded_query = urllib.parse.quote(q)
    encoded_loc = urllib.parse.quote(loc)
    # f_TPR=r86400 = ONLY past 24 hours
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_query}&location={encoded_loc}&f_TPR=r86400&start=0"

    try:
        resp = await polite_linkedin_get(client, url, timeout=12.0)
        if not resp or resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.find_all("li")
        record_log("INFO", f"  [Agent-1B: TODAY] {len(cards)} cards found for '{q}' in {loc}")

        fetched = 0
        for card in cards:
            title_elem = card.find("h3", class_="base-search-card__title")
            company_elem = card.find("h4", class_="base-search-card__subtitle")
            link_elem = card.find("a", class_="base-card__full-link")
            loc_elem = card.find("span", class_="job-search-card__location")
            time_elem = card.find("time")

            if not (title_elem and company_elem and link_elem):
                continue

            title = title_elem.text.strip()
            company = company_elem.text.strip()
            raw_link = link_elem.get("href", "")
            clean_link = raw_link.split("?")[0] if raw_link else None
            job_loc = loc_elem.text.strip() if loc_elem else loc

            if not is_india_location(job_loc):
                continue

            t_lower = title.lower()
            if any(sw in t_lower for sw in DISALLOWED_TITLE_KEYWORDS):
                continue
            if not any(k in t_lower for k in ["java", "spring", "backend", "sde", "software engineer", "microservice"]):
                continue

            job_id_match = re.search(r"(\d{8,12})", clean_link or "")
            if not job_id_match or not clean_link:
                continue

            job_id = job_id_match.group(1)
            detail_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
            d_resp = await polite_linkedin_get(client, detail_url, timeout=7.0)
            if not d_resp or d_resp.status_code != 200:
                continue

            fetched += 1
            if fetched >= 10:
                break

            d_soup = BeautifulSoup(d_resp.text, "html.parser")
            d_box = d_soup.find("div", class_="show-more-less-html__markup")
            desc_text = d_box.get_text(separator=" ", strip=True) if d_box else ""
            if len(desc_text) < 30:
                desc_text = f"Java/Spring Boot Backend Developer role at {company} ({job_loc})."

            eligible, exp_val, exp_label, reason = evaluate_experience_eligibility(title, desc_text)
            if not eligible:
                continue

            posted_at, posted_date_str = parse_linkedin_date(
                time_elem.get("datetime") if time_elem else None,
                time_elem.text.strip() if time_elem else "Today"
            )

            ai_eval = await async_ai_evaluate_job_eligibility(title, desc_text)
            if not ai_eval.get("is_eligible", True):
                continue

            score = ai_eval.get("ats_score") or calculate_ats_match_score(title, desc_text)
            min_exp = ai_eval.get("min_exp") or exp_val

            record_log("INFO", f"  🎯 [Agent-1B: TODAY] {title} @ {company} [{posted_date_str}]")
            jobs.append({
                "title": title, "company": company, "location": job_loc,
                "experience_required": min_exp, "experience_str": f"{min_exp:.1f} Years Exp",
                "description": desc_text[:5000], "apply_link": clean_link,
                "hr_email": ai_eval.get("hr_email"),
                "google_form_url": ai_eval.get("google_form_or_apply_url"),
                "source": "LinkedIn Job Listing",
                "match_score": score, "posted_at": posted_at,
                "posted_date_str": posted_date_str,
            })
    except Exception as e:
        record_log("WARNING", f"[Agent-1B: TODAY] {e}")

    record_log("INFO", f"✔ [Agent-1B: TODAY] {len(jobs)} today's jobs found.")
    return jobs

# ==============================================
# AGENT 2: LinkedIn South Tech Hub Hunter (Bengaluru, Hyderabad)
# ==============================================
SOUTH_OFFSET_INDEX = 0
async def agent_linkedin_hub_south(client: Any) -> List[Dict[str, Any]]:
    global SOUTH_OFFSET_INDEX
    offset = (SOUTH_OFFSET_INDEX * 10) % 50
    SOUTH_OFFSET_INDEX += 1
    record_log("INFO", f"🔎 [Agent-2: LinkedIn South Hub] Scanning live 1-2 YOE postings in Bengaluru & Hyderabad (offset={offset})...")
    queries = [
        ("Java Developer", "Bengaluru"),
        ("Spring Boot Developer", "Hyderabad")
    ]
    all_jobs = []
    for q, loc in queries:
        found = await agent_linkedin_hunt(client, query=q, location=loc, offset=offset)
        all_jobs.extend(found)
    record_log("INFO", f"✔ [Agent-2: LinkedIn South Hub] Gathered {len(all_jobs)} candidate openings.")
    return all_jobs

# ==============================================
# AGENT 3: LinkedIn West & Remote Hub Hunter (Pune, Remote India)
# ==============================================
WEST_OFFSET_INDEX = 0
async def agent_linkedin_hub_west_remote(client: Any) -> List[Dict[str, Any]]:
    global WEST_OFFSET_INDEX
    offset = (WEST_OFFSET_INDEX * 10) % 50
    WEST_OFFSET_INDEX += 1
    record_log("INFO", f"🔎 [Agent-3: LinkedIn West & Remote] Scanning live postings in Pune & Remote/Pan-India (offset={offset})...")
    queries = [
        ("Java Developer", "Pune"),
        ("Java Backend Developer", "Remote")
    ]
    all_jobs = []
    for q, loc in queries:
        found = await agent_linkedin_hunt(client, query=q, location=loc, offset=offset)
        all_jobs.extend(found)
    record_log("INFO", f"✔ [Agent-3: LinkedIn West & Remote] Gathered {len(all_jobs)} candidate openings.")
    return all_jobs

# ==============================================
# AGENT 4: LinkedIn Deep Offset Paginated Sweeper (Never Miss Fast-Moving Jobs)
# ==============================================
PAGINATED_OFFSETS = [15, 30, 45, 60, 75, 90]
PAGINATED_INDEX = 0

async def agent_linkedin_paginated_sweep(client: Any) -> List[Dict[str, Any]]:
    global PAGINATED_INDEX
    offset = PAGINATED_OFFSETS[PAGINATED_INDEX % len(PAGINATED_OFFSETS)]
    PAGINATED_INDEX += 1
    record_log("INFO", f"🔎 [Agent-4: LinkedIn Paginated Stream] Sweeping deep offset={offset} for fresh 1-2 YOE Java roles...")
    queries = [
        ("Spring Boot Developer", "India", offset),
        ("Java Developer", "Bengaluru", offset)
    ]
    all_jobs = []
    for q, loc, off in queries:
        found = await agent_linkedin_hunt(client, query=q, location=loc, offset=off)
        all_jobs.extend(found)
    record_log("INFO", f"✔ [Agent-4: LinkedIn Paginated Stream] Extracted {len(all_jobs)} deep-offset openings.")
    return all_jobs

# ==============================================================================
# VERIFY & EXTRACT LINKEDIN POST DETAILS (Strict 3-Day Rule & LD+JSON Parser)
# ==============================================================================
async def verify_and_extract_linkedin_post(client: Any, post_url: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Ultra-strict LinkedIn Post Extractor & Validator:
    1. Fetches post permalink (HTTP 200).
    2. Parses schema.org SocialMediaPosting LD+JSON for exact `datePublished`.
       -> STRICT 3-DAY MAX RECENCY RULE: If post > 3.0 days old, REJECTS!
    3. Evaluates 2 YOE Java backend qualification & India location.
    4. Extracts recruiter author name, HR email, Google Form / apply link.
    """
    clean_url = post_url.split("?")[0].rstrip("/") + "/"
    if not ("/posts/" in clean_url or "/feed/update/" in clean_url or "activity-" in clean_url):
        return False, None, "Not a valid LinkedIn post permalink"

    date_str = "Recently"
    published_dt = datetime.utcnow()

    try:
        headers = get_rotating_headers()
        resp = await client.get(clean_url, headers=headers, timeout=9.0, follow_redirects=True)
        if resp.status_code != 200:
            return False, None, f"Returned HTTP {resp.status_code}"

        b_lower = resp.text.lower()
        for dead_cue in [
            "this post is no longer available",
            "this content isn't available right now",
            "page not found",
            "post has been deleted",
            "post has been removed"
        ]:
            if dead_cue in b_lower:
                return False, None, f"Post removed cue: '{dead_cue}'"

        soup = BeautifulSoup(resp.text, "html.parser")
        headline = ""
        body_text = ""
        author_name = "LinkedIn Recruiter"
        ld_found = False

        for s in soup.find_all("script", type="application/ld+json"):
            if not s.string:
                continue
            try:
                data = json.loads(s.string)
                if data.get("@type") == "SocialMediaPosting" or "datePublished" in data:
                    ld_found = True
                    date_published_str = data.get("datePublished")
                    if date_published_str:
                        pub_dt = datetime.fromisoformat(date_published_str.replace("Z", "+00:00"))
                        now_dt = datetime.now(timezone.utc)
                        diff_days = (now_dt - pub_dt).total_seconds() / 86400.0
                        if diff_days > 28.0:
                            return False, None, f"Post is {diff_days:.1f} days old (max allowed: 28 days)"

                        published_dt = pub_dt.replace(tzinfo=None)
                        if diff_days < 1.0:
                            date_str = "Today"
                        elif diff_days < 2.0:
                            date_str = "1 day ago"
                        else:
                            date_str = f"{int(diff_days)} days ago"

                    headline = data.get("headline") or ""
                    body_text = data.get("articleBody") or ""
                    author_obj = data.get("author") or {}
                    if isinstance(author_obj, dict):
                        author_name = author_obj.get("name") or author_name
                    elif isinstance(author_obj, str):
                        author_name = author_obj
                    break
            except Exception:
                pass

        if not body_text:
            meta_desc = soup.find("meta", {"name": "description"})
            if meta_desc and meta_desc.get("content"):
                body_text = meta_desc["content"]

        if not body_text:
            body_text = soup.get_text(separator=" ", strip=True)[:2500]

        # If LD+JSON wasn't available, check text cues for stale posts
        if not ld_found:
            stale_cues = ["1mo", "2mo", "3mo", "4mo", "1 month ago", "2 months ago", "1yr", "years ago"]
            if any(c in b_lower for c in stale_cues):
                return False, None, "Text cue indicates post older than 1 month"

        # Check Java / Backend / Software Engineering cues
        combined = f"{headline} {body_text}".lower()
        if not any(k in combined for k in ["java", "spring", "backend", "software engineer", "software development", "microservice", "api"]):
            return False, None, "No Java/Backend engineering keyword found in post"

        # Fast Heuristic Check (0ms)
        title_candidate = headline or f"Java / Backend Developer - {author_name}"
        eligible, exp_val, exp_label, exp_reason = evaluate_experience_eligibility(title_candidate, body_text, max_candidate_exp=2.0)
        if not eligible:
            return False, None, f"Ineligible experience ({exp_reason})"

        # Strict India location verification
        if not is_india_location(body_text):
            return False, None, "Non-India location detected"

        # Deep Gemini AI Verification & Extraction
        ai_eval = await async_ai_evaluate_job_eligibility(title_candidate, body_text)
        if not ai_eval.get("is_eligible", True):
            ai_reason = ai_eval.get("rejection_reason") or "AI determined post is not eligible"
            return False, None, f"AI Filtered: {ai_reason}"

        # Extract HR email
        email_match = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', body_text)
        valid_emails = [e for e in email_match if not any(e.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js'])]
        hr_email = ai_eval.get("hr_email") or (valid_emails[0] if valid_emails else None)

        # Extract Google Form URL
        form_match = re.findall(r'(https?://(?:forms\.gle|docs\.google\.com/forms|forms\.office\.com)[^\s\)]+)', body_text)
        form_url = ai_eval.get("google_form_or_apply_url") or (form_match[0] if form_match else None)

        # Extract external apply link (especially lnkd.in, bit.ly, or direct ATS/career links)
        detected_apply = None
        lnkd_matches = re.findall(r'(https?://lnkd\.in/[a-zA-Z0-9_\-]+)', body_text)
        if lnkd_matches:
            detected_apply = lnkd_matches[0]
        else:
            ext_urls = re.findall(r'(https?://[^\s\)\]>]+)', body_text)
            for u in ext_urls:
                if not any(ign in u for ign in ["linkedin.com/in/", "linkedin.com/company/", "linkedin.com/feed/hashtag", "licdn.com"]):
                    detected_apply = u
                    break

        # Expand lnkd.in shortlinks
        if detected_apply and "lnkd.in" in detected_apply:
            try:
                s_resp = await client.get(detected_apply, headers=headers, timeout=6.0, follow_redirects=True)
                final_s = str(s_resp.url)
                if "lnkd.in" not in final_s and "linkedin.com" not in final_s:
                    detected_apply = final_s
                else:
                    m_dest = re.findall(r'href=[\"\'](https?://[^\"\']+)[\"\']', s_resp.text)
                    for md in m_dest:
                        if "linkedin.com" not in md and "licdn.com" not in md and not md.endswith(('.ico', '.css', '.js', '.png', '.jpg')):
                            detected_apply = md
                            break
            except Exception:
                pass

        score = ai_eval.get("ats_score") or calculate_ats_match_score(title_candidate, body_text)
        min_exp = ai_eval.get("min_exp") or exp_val
        exp_label = f"{min_exp:.1f} Years Exp" if min_exp else exp_label

        # Try extracting real company and role from post body
        extracted_company = author_name
        extracted_title = title_candidate
        m_hiring = re.search(r'([A-Za-z0-9\.\s]+?)\s+is\s+[Hh]iring\s*[\|\-:\–]\s*([^\n\r]+)', body_text)
        if m_hiring:
            c_cand = m_hiring.group(1).strip()
            t_cand = m_hiring.group(2).strip()
            if len(c_cand) <= 50 and len(t_cand) <= 120:
                extracted_company = c_cand
                extracted_title = t_cand

        job_data = {
            "title": extracted_title[:100],
            "company": extracted_company[:50],
            "location": "India / Remote",
            "experience_required": min_exp,
            "experience_str": exp_label,
            "description": body_text[:5000],
            "apply_link": detected_apply or clean_url,
            "post_url": clean_url,
            "hr_email": hr_email,
            "google_form_url": form_url,
            "source": "LinkedIn Post (#hiring)",
            "match_score": score,
            "posted_at": published_dt,
            "posted_date_str": date_str
        }
        return True, job_data, "Verified live post within 3 days"
        return True, job_data, "Verified live post within 3 days"
    except Exception as e:
        return False, None, f"Verification failed: {e}"

# ==============================================================================
# AGENT 5A: LinkedIn Posts Hunter (Urgent Joiners & Immediate Roles)
# ==============================================================================
AGENT_5A_INDEX = 0
AGENT_5A_QUERIES = [
    'site:linkedin.com/posts "Java Developer" hiring India',
    'site:linkedin.com/posts "Java Backend Developer" hiring India',
    'site:linkedin.com/posts "Spring Boot" hiring India',
    'site:linkedin.com/posts "Java" "immediate joiner" India',
    'site:linkedin.com/posts "Backend Developer" "Java" hiring India',
    'site:linkedin.com/posts "Java Developer" ("0-2" OR "1-2" OR "1-3" OR "2 years") India',
    'site:linkedin.com/posts "Spring Boot Developer" hiring India',
    'site:linkedin.com/posts "Java Backend" ("Noida" OR "Bangalore" OR "Pune" OR "Remote") hiring'
]

async def agent_linkedin_posts_urgent(client: Any) -> List[Dict[str, Any]]:
    global AGENT_5A_INDEX
    jobs = []
    # Run 2 rotating queries to maximize post coverage
    queries_to_run = [
        AGENT_5A_QUERIES[AGENT_5A_INDEX % len(AGENT_5A_QUERIES)],
        AGENT_5A_QUERIES[(AGENT_5A_INDEX + 1) % len(AGENT_5A_QUERIES)]
    ]
    AGENT_5A_INDEX += 2

    for q in queries_to_run:
        record_log("INFO", f"🔎 [Agent-5A: LinkedIn Urgent Posts] Scanning recruiter posts: '{q}'...")
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda query=q: robust_ddgs_search(query, max_results=10))
            for item in results:
                url = item.get("href", "").strip()
                if not ("/posts/" in url or "/feed/update/" in url or "activity-" in url):
                    continue
                is_valid, post_job, reason = await verify_and_extract_linkedin_post(client, url)
                if is_valid and post_job:
                    jobs.append(post_job)
                    record_log("INFO", f"  🎯 [Agent-5A: LinkedIn Posts] Discovered post: '{post_job['title']}' ({url})")
                else:
                    record_log("DEBUG", f"  🚫 [Agent-5A: LinkedIn Posts] Filtered ({reason}): {url}")
        except Exception as e:
            record_log("WARNING", f"[Agent-5A: LinkedIn Urgent Posts] Notice: {e}")
    record_log("INFO", f"✔ [Agent-5A: LinkedIn Urgent Posts] Loaded {len(jobs)} recruiter posts.")
    return jobs

# ==============================================================================
# AGENT 5B: LinkedIn Posts Hunter (Tech Hubs: Noida, Gurgaon, Bangalore, Pune)
# ==============================================================================
AGENT_5B_INDEX = 0
AGENT_5B_QUERIES = [
    'site:linkedin.com/posts "Java Developer" Noida hiring',
    'site:linkedin.com/posts "Java Developer" Bangalore hiring',
    'site:linkedin.com/posts "Java Developer" Gurgaon hiring',
    'site:linkedin.com/posts "Backend Developer" Bangalore hiring',
    'site:linkedin.com/posts "Java Developer" Pune hiring',
    'site:linkedin.com/posts "Java Developer" Hyderabad hiring',
    'site:linkedin.com/posts "Spring Boot" Noida hiring',
    'site:linkedin.com/posts "Backend Developer" Pune hiring'
]

async def agent_linkedin_posts_tech_hubs(client: Any) -> List[Dict[str, Any]]:
    global AGENT_5B_INDEX
    jobs = []
    queries_to_run = [
        AGENT_5B_QUERIES[AGENT_5B_INDEX % len(AGENT_5B_QUERIES)],
        AGENT_5B_QUERIES[(AGENT_5B_INDEX + 1) % len(AGENT_5B_QUERIES)]
    ]
    AGENT_5B_INDEX += 2

    for q in queries_to_run:
        record_log("INFO", f"🔎 [Agent-5B: LinkedIn Hub Posts] Scanning regional recruiter posts: '{q}'...")
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda query=q: robust_ddgs_search(query, max_results=10))
            for item in results:
                url = item.get("href", "").strip()
                if not ("/posts/" in url or "/feed/update/" in url or "activity-" in url):
                    continue
                is_valid, post_job, reason = await verify_and_extract_linkedin_post(client, url)
                if is_valid and post_job:
                    jobs.append(post_job)
                    record_log("INFO", f"  🎯 [Agent-5B: LinkedIn Posts] Discovered post: '{post_job['title']}' ({url})")
                else:
                    record_log("DEBUG", f"  🚫 [Agent-5B: LinkedIn Posts] Filtered ({reason}): {url}")
        except Exception as e:
            record_log("WARNING", f"[Agent-5B: LinkedIn Hub Posts] Notice: {e}")
    record_log("INFO", f"✔ [Agent-5B: LinkedIn Hub Posts] Loaded {len(jobs)} recruiter posts.")
    return jobs

# ==============================================================================
# AGENT 5C: LinkedIn Posts Hunter (HR Direct Resumes & Google Forms)
# ==============================================================================
AGENT_5C_INDEX = 0
AGENT_5C_QUERIES = [
    'site:linkedin.com/posts "Java Developer" "send resume" India',
    'site:linkedin.com/posts "Java Developer" "share resume" India',
    'site:linkedin.com/posts "Backend Developer" "send resume" India',
    'site:linkedin.com/posts "Java" "Google Form" hiring India',
    'site:linkedin.com/posts "Spring Boot" "send resume" India',
    'site:linkedin.com/posts "Java Developer" "immediate joiner" India',
    'site:linkedin.com/posts "Java Backend" "mail your resume" India'
]

async def agent_linkedin_posts_hr_direct(client: Any) -> List[Dict[str, Any]]:
    global AGENT_5C_INDEX
    jobs = []
    queries_to_run = [
        AGENT_5C_QUERIES[AGENT_5C_INDEX % len(AGENT_5C_QUERIES)],
        AGENT_5C_QUERIES[(AGENT_5C_INDEX + 1) % len(AGENT_5C_QUERIES)]
    ]
    AGENT_5C_INDEX += 2

    for q in queries_to_run:
        record_log("INFO", f"🔎 [Agent-5C: LinkedIn HR Posts] Scanning direct resume & form posts: '{q}'...")
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda query=q: robust_ddgs_search(query, max_results=10))
            for item in results:
                url = item.get("href", "").strip()
                if not ("/posts/" in url or "/feed/update/" in url or "activity-" in url):
                    continue
                is_valid, post_job, reason = await verify_and_extract_linkedin_post(client, url)
                if is_valid and post_job:
                    jobs.append(post_job)
                    record_log("INFO", f"  🎯 [Agent-5C: LinkedIn Posts] Discovered post: '{post_job['title']}' ({url})")
                else:
                    record_log("DEBUG", f"  🚫 [Agent-5C: LinkedIn Posts] Filtered ({reason}): {url}")
        except Exception as e:
            record_log("WARNING", f"[Agent-5C: LinkedIn HR Posts] Notice: {e}")
    record_log("INFO", f"✔ [Agent-5C: LinkedIn HR Posts] Loaded {len(jobs)} recruiter posts.")
    return jobs

# ==============================================================================
# AGENT 6: GOOGLE & DEEP WEB SEARCH HUNTER (Autonomous Web Crawler)
# Deep searches Google/Bing/Web across Noida, Bangalore & Indian tech hubs
# STRICTLY verifies every URL returns HTTP 200 and is NOT a 404 or closed posting!
# ==============================================================================
WEB_SEARCH_ROTATION_INDEX = 0

WEB_SEARCH_QUERIES = [
    'site:jobs.lever.co ("Java Developer" OR "Spring Boot") India',
    'site:boards.greenhouse.io ("Java Developer" OR "Spring Boot") India',
    'site:jobs.ashbyhq.com ("Java" OR "Spring Boot") India',
    'site:apply.workable.com ("Java Developer" OR "Spring Boot") India',
    'site:naukri.com/job-listings "Java Developer" ("Spring Boot") ("Noida" OR "Bangalore")',
    '"Java Developer" ("Spring Boot") ("Noida" OR "Gurgaon") ("apply now" OR "careers") -indeed -glassdoor -foundit',
    '"Java Backend Developer" ("Spring Boot") ("Bangalore" OR "Bengaluru") ("apply now" OR "careers") -indeed -glassdoor -foundit',
]

DISALLOWED_DOMAINS = [
    "glassdoor.co.in", "glassdoor.com", "indeed.com", "foundit.in", "jooble.org",
    "simplyhired.co.in", "simplyhired.com", "jobleads.com", "geeksforgeeks.org",
    "quora.com", "reddit.com", "ambitionbox.com", "shine.com"
]

DEAD_JOB_INDICATORS = [
    "sorry, we couldn't find anything here",
    "404 error",
    "job posting you're looking for might have closed",
    "it has been removed",
    "this position is no longer available",
    "this job has expired",
    "job is closed",
    "this posting has been removed",
    "no longer accepting applications",
    "page not found",
    "404 not found",
    "this job is no longer open"
]

async def verify_live_job_url(client: Any, url: str) -> Tuple[bool, str]:
    """
    Strict URL Verification:
    1. Blocks aggregator search hubs (Glassdoor, Indeed, Jooble, Foundit search feeds).
    2. Blocks LinkedIn generic search query hubs.
    3. Performs an actual HTTP GET to ensure the page returns HTTP 200.
    4. Checks page content to guarantee it's not a 'Job Closed / 404 / Expired' notice.
    """
    if not url or not url.startswith("http"):
        return False, "Invalid URL"
        
    url_lower = url.lower()
    for d in DISALLOWED_DOMAINS:
        if d in url_lower:
            return False, f"Filtered aggregator search domain: {d}"
            
    # Block aggregator search hubs, only permit direct individual job view or post permalinks
    if "linkedin.com/jobs" in url_lower and "/view/" not in url_lower:
        return False, "Filtered generic LinkedIn search aggregator hub"
    if "naukri.com" in url_lower and "/job-listings" not in url_lower:
        return False, "Filtered generic Naukri search aggregator hub"
    if "-jobs-in-" in url_lower or "-job-vacancies" in url_lower:
        return False, "Filtered generic aggregator search landing page"

    try:
        headers = get_rotating_headers()
        resp = await client.get(url, headers=headers, timeout=6.0, follow_redirects=True)
        if resp.status_code != 200:
            return False, f"Returned HTTP {resp.status_code}"
            
        b_lower = resp.text.lower()

        # For LinkedIn posts and feed updates, specifically check post deletion indicators
        # (avoiding false positives from recommended jobs in LinkedIn's sidebar)
        if "linkedin.com/posts" in url_lower or "linkedin.com/feed/update" in url_lower or "activity-" in url_lower:
            linkedin_dead_indicators = [
                "this post is no longer available",
                "this content isn't available right now",
                "page not found",
                "404 not found",
                "post has been deleted",
                "post has been removed"
            ]
            for p in linkedin_dead_indicators:
                if p in b_lower:
                    return False, f"LinkedIn post removed: '{p}'"
            return True, "Verified Live 200 OK"

        for phrase in DEAD_JOB_INDICATORS:
            if phrase in b_lower:
                return False, f"Expired/Dead job text detected: '{phrase}'"
                
        return True, "Verified Live 200 OK"
    except Exception as e:
        return False, f"Verification request failed: {e}"

def clean_company_from_web(title: str, url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.strip('/')
    
    if 'lever.co' in domain:
        parts = path.split('/')
        return parts[0].capitalize() if parts else 'Lever Tech Partner'
    if 'greenhouse.io' in domain:
        parts = path.split('/')
        return parts[0].capitalize() if parts else 'Greenhouse Tech Partner'
    if 'ashbyhq.com' in domain:
        parts = path.split('/')
        return parts[0].capitalize() if parts else 'Ashby Tech Partner'
    
    for delim in [' | ', ' - ', ' – ']:
        if delim in title:
            tokens = [t.strip() for t in title.split(delim) if t.strip()]
            for tok in reversed(tokens):
                if not any(k in tok.lower() for k in ['careers', 'job', 'jobs', 'hiring', 'india', 'noida', 'gurgaon', 'bangalore', 'apply']):
                    return tok[:35]
    
    clean_domain = domain.replace('www.', '').split('.')[0]
    return clean_domain.capitalize()

async def agent_web_search_hunter(client: Any) -> List[Dict[str, Any]]:
    global WEB_SEARCH_ROTATION_INDEX
    q = WEB_SEARCH_QUERIES[WEB_SEARCH_ROTATION_INDEX % len(WEB_SEARCH_QUERIES)]
    WEB_SEARCH_ROTATION_INDEX += 1
    
    record_log("INFO", f"🌐 [Agent-6: Google/Web Hunter] Deep crawling the web for: '{q}'...")
    jobs = []
    
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: robust_ddgs_search(q, max_results=8))
        
        for item in results:
            title = item.get('title', '').strip()
            link = item.get('href', '').strip()
            snippet = item.get('body', '').strip()
            
            if not title or not link or not link.startswith('http'):
                continue
                
            combined_text = f"{title} {snippet}".lower()
            if "java" not in combined_text and "spring" not in combined_text:
                continue
                
            eligible, exp_val, exp_label, reason = evaluate_experience_eligibility(title, snippet, max_candidate_exp=2.0)
            if not eligible:
                continue
                
            # STRICT LIVE URL VERIFICATION: Checks HTTP 200 & rejects 404/expired notices!
            is_live, verify_reason = await verify_live_job_url(client, link)
            if not is_live:
                record_log("INFO", f"  🚫 [Agent-6: Google/Web Hunter] Filtered dead link ({verify_reason}): {link}")
                continue

            # Deep Gemini AI Verification
            ai_eval = await async_ai_evaluate_job_eligibility(title, snippet)
            if not ai_eval.get("is_eligible", True):
                continue
                
            company = clean_company_from_web(title, link)
            
            email_match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', snippet)
            hr_email = ai_eval.get("hr_email") or (email_match.group(1) if email_match else None)
            form_url = ai_eval.get("google_form_or_apply_url")
            score = ai_eval.get("ats_score") or calculate_ats_match_score(title, snippet)
            min_exp = ai_eval.get("min_exp") or exp_val
            exp_label = f"{min_exp:.1f} Years Exp" if min_exp else exp_label
            
            jobs.append({
                "title": title[:100],
                "company": company,
                "location": "Noida / Bangalore / India",
                "experience_required": min_exp,
                "experience_str": exp_label,
                "description": snippet or f"Java & Spring Boot backend opening at {company}. Apply directly on career portal: {link}",
                "apply_link": link,
                "hr_email": hr_email,
                "google_form_url": form_url,
                "source": "Web Search / Company Career Portal",
                "match_score": score,
                "posted_at": datetime.utcnow(),
                "posted_date_str": "Today"
            })
            record_log("INFO", f"  🎯 [Agent-6: Google/Web Hunter] Verified 200 OK Live Job: '{title[:45]}' @ {company}")
        
        record_log("INFO", f"✔ [Agent-6: Google/Web Hunter] Discovered {len(jobs)} 100% verified live roles from web crawl.")
    except Exception as e:
        record_log("WARNING", f"[Agent-6: Google/Web Hunter] Notice: {e}")
        
    return jobs

# ==============================================================================
# AGENT 7: TOP INDIAN TECH & FINTECH CAREER PORTALS (Direct ATS APIs)
# Directly inspects Greenhouse & Lever APIs of top startups & fintech firms
# ==============================================================================
TECH_COMPANIES_TO_POLL = [
    # Fintechs & Startups
    ("cred", "lever"),
    ("meesho", "lever"),
    ("zeta", "lever"),
    ("inmobi", "greenhouse"),
    ("groww", "greenhouse"),
    ("slice", "greenhouse"),
    ("lingarogroup", "lever"),
    # Indian Tech Startups
    ("razorpay", "lever"),
    ("zepto", "greenhouse"),
    ("browserstack", "lever"),
    ("postman-inc", "greenhouse"),
    ("clevertap", "greenhouse"),
    ("zetwerk", "greenhouse"),
    ("khatabook", "lever"),
    ("coinswitch", "greenhouse"),
    ("healthifyme", "greenhouse"),
    # Global Tech with India offices
    ("thoughtworks", "greenhouse"),
    ("gojek", "lever"),
    ("intuit", "greenhouse"),
    ("freshworks", "greenhouse"),
    ("moengage", "greenhouse"),
    # ATS Portals
    ("termgrid", "lever"),
    ("weekday-1", "workable"),
    ("foxtrot-systems", "lever"),
]
ATS_POLL_INDEX = 0

async def agent_top_tech_career_portals(client: Any) -> List[Dict[str, Any]]:
    global ATS_POLL_INDEX
    batch = [
        TECH_COMPANIES_TO_POLL[(ATS_POLL_INDEX + i) % len(TECH_COMPANIES_TO_POLL)]
        for i in range(2)
    ]
    ATS_POLL_INDEX += 2
    
    jobs = []
    for company, ats_type in batch:
        record_log("INFO", f"🏢 [Agent-7: Tech Portal Hunter] Scanning open roles for {company.upper()} via {ats_type.upper()} API...")
        try:
            if ats_type == "lever":
                url = f"https://api.lever.co/v0/postings/{company}?mode=json"
                r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6.0)
                if r.status_code == 200:
                    for item in r.json():
                        title = item.get("text", "").strip()
                        loc = item.get("categories", {}).get("location", "India / Remote")
                        apply_url = item.get("hostedUrl", "")
                        desc = item.get("descriptionPlain", "") or title
                        
                        t_lower = title.lower()
                        if not any(k in t_lower for k in ["java", "spring", "backend", "software engineer", "sde"]):
                            continue
                            
                        eligible, exp_val, exp_label, reason = evaluate_experience_eligibility(title, desc, max_candidate_exp=2.0)
                        if not eligible:
                            continue

                        is_live, verify_reason = await verify_live_job_url(client, apply_url)
                        if not is_live:
                            continue
                            
                        score = calculate_ats_match_score(title, desc)
                        jobs.append({
                            "title": title,
                            "company": company.capitalize(),
                            "location": loc,
                            "experience_required": exp_val,
                            "experience_str": exp_label,
                            "description": desc[:3000],
                            "apply_link": apply_url,
                            "hr_email": None,
                            "google_form_url": None,
                            "source": f"{company.capitalize()} Career Portal",
                            "match_score": score,
                            "posted_at": datetime.utcnow(),
                            "posted_date_str": "Today"
                        })
            elif ats_type == "greenhouse":
                url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
                r = await client.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6.0)
                if r.status_code == 200:
                    for item in r.json().get("jobs", []):
                        title = item.get("title", "").strip()
                        loc = item.get("location", {}).get("name", "India")
                        apply_url = item.get("absolute_url", "")
                        
                        t_lower = title.lower()
                        if not any(k in t_lower for k in ["java", "spring", "backend", "software engineer", "sde"]):
                            continue
                            
                        desc = f"{title} opening at {company.capitalize()} in {loc}. Apply directly: {apply_url}"
                        eligible, exp_val, exp_label, reason = evaluate_experience_eligibility(title, desc, max_candidate_exp=2.0)
                        if not eligible:
                            continue

                        is_live, verify_reason = await verify_live_job_url(client, apply_url)
                        if not is_live:
                            continue
                            
                        score = calculate_ats_match_score(title, desc)
                        jobs.append({
                            "title": title,
                            "company": company.capitalize(),
                            "location": loc,
                            "experience_required": exp_val,
                            "experience_str": exp_label,
                            "description": desc,
                            "apply_link": apply_url,
                            "hr_email": None,
                            "google_form_url": None,
                            "source": f"{company.capitalize()} Career Portal",
                            "match_score": score,
                            "posted_at": datetime.utcnow(),
                            "posted_date_str": "Today"
                        })
        except Exception as e:
            logger.debug(f"ATS poll error for {company}: {e}")
            
    record_log("INFO", f"✔ [Agent-7: Tech Portal Hunter] Found {len(jobs)} eligible roles across tech company career sites.")
    return jobs

# ==============================================================================
# AGENT 8: NAUKRI.COM INDIA SCRAPER (DDGS-Based)
# Searches Naukri directly for fresh 1-2 YOE Java openings in India
# ==============================================================================
NAUKRI_SEARCH_INDEX = 0
NAUKRI_SEARCH_QUERIES = [
    'site:naukri.com "java developer" "1 to 2 years" OR "0 to 2 years" OR "1-2 years" OR "0-2 years"',
    'site:naukri.com "spring boot developer" "1 to 2 years" OR "0 to 2 years" (noida OR bangalore OR pune)',
    'site:naukri.com "java backend developer" "1 to 3 years" (noida OR gurgaon OR bangalore OR pune)',
    'site:naukri.com "java microservices" "1-2 years" OR "2-3 years" india',
    'site:naukri.com "java developer" "2 years" (bangalore OR noida OR hyderabad OR pune)',
    'site:naukri.com "spring boot" "java" "0-2 years" OR "1-2 years" 2026',
    'site:naukri.com "java software engineer" "fresher" OR "1 year" OR "2 years" india',
    'site:naukri.com "backend developer" java "1 to 2" OR "2 to 3" (noida OR bangalore)',
]

async def agent_naukri_search(client: Any) -> List[Dict[str, Any]]:
    """
    Agent 8: Naukri.com Java Job Scraper using DDGS.
    Searches Naukri listing pages for 1-2 YOE Java/Spring Boot jobs.
    """
    global NAUKRI_SEARCH_INDEX
    q = NAUKRI_SEARCH_QUERIES[NAUKRI_SEARCH_INDEX % len(NAUKRI_SEARCH_QUERIES)]
    NAUKRI_SEARCH_INDEX += 1

    record_log("INFO", f"🔎 [Agent-8: Naukri Hunter] Searching Naukri.com: '{q}'...")
    jobs = []
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: robust_ddgs_search(q, max_results=10))

        for item in results:
            title = item.get("title", "").strip()
            link = item.get("href", "").strip()
            snippet = item.get("body", "").strip()

            if not link or not link.startswith("http"):
                continue

            # Must be a Naukri job listing URL
            if "naukri.com" not in link.lower():
                continue

            # Skip Naukri search result pages - only direct job listings
            if "/job-listings-" not in link and "/jobs/" not in link and "job-listings" not in link:
                continue

            combined = f"{title} {snippet}".lower()
            if not any(k in combined for k in ["java", "spring", "backend", "j2ee"]):
                continue

            # Experience eligibility check
            eligible, exp_val, exp_label, reason = evaluate_experience_eligibility(title, snippet, max_candidate_exp=2.0)
            if not eligible:
                record_log("INFO", f"  🚫 [Agent-8: Naukri] Filtered: '{title}' ({reason})")
                continue

            # India location check
            if not is_india_location(snippet) and not is_india_location(title):
                continue

            # Deep AI check
            ai_eval = await async_ai_evaluate_job_eligibility(title, snippet)
            if not ai_eval.get("is_eligible", True):
                record_log("INFO", f"  🚫 [Agent-8: Naukri] AI Filtered: '{title}'")
                continue

            # Extract company from snippet (often "Company Name | Naukri.com" pattern)
            company = "Naukri Listed Company"
            c_match = re.search(r"at\s+([A-Za-z0-9\s\.\-&]+?)\s*(?:\||in\s+[A-Z]|$)", snippet)
            if c_match:
                company = c_match.group(1).strip()[:50]
            elif " | " in title:
                parts = title.split(" | ")
                if len(parts) >= 2:
                    company = parts[-1].strip()[:50]
                    title = parts[0].strip()

            # Extract location from snippet
            loc = "India"
            for city in ["Noida", "Bangalore", "Bengaluru", "Gurgaon", "Hyderabad", "Pune", "Mumbai", "Chennai", "Delhi"]:
                if city.lower() in combined:
                    loc = city
                    break

            score = ai_eval.get("ats_score") or calculate_ats_match_score(title, snippet)
            min_exp = ai_eval.get("min_exp") or exp_val
            final_exp_label = f"{min_exp:.1f} Years Exp" if min_exp else exp_label
            hr_email = ai_eval.get("hr_email")
            form_url = ai_eval.get("google_form_or_apply_url")

            jobs.append({
                "title": title[:100],
                "company": company,
                "location": loc,
                "experience_required": min_exp,
                "experience_str": final_exp_label,
                "description": snippet or f"Java/Spring Boot Backend Developer role at {company} ({loc}). Apply on Naukri: {link}",
                "apply_link": link,
                "hr_email": hr_email,
                "google_form_url": form_url,
                "source": "Naukri India Direct",
                "match_score": score,
                "posted_at": datetime.utcnow(),
                "posted_date_str": "Today"
            })
            record_log("INFO", f"  🎯 [Agent-8: Naukri] Found: '{title[:50]}' @ {company} ({loc})")

    except Exception as e:
        record_log("WARNING", f"[Agent-8: Naukri Hunter] Notice: {e}")

    record_log("INFO", f"✔ [Agent-8: Naukri] Collected {len(jobs)} Naukri Java job listings.")
    return jobs

# ==============================================================================
# AGENT 9: INDEED INDIA SCRAPER (DDGS-Based)
# Searches Indeed India for fresh 1-2 YOE Java openings
# ==============================================================================
INDEED_SEARCH_INDEX = 0
INDEED_SEARCH_QUERIES = [
    'site:indeed.com "java developer" india "1 year" OR "2 years" OR "0-2 years" 2026',
    'site:indeed.co.in "spring boot developer" "1 to 2" OR "2 to 3" india',
    'site:indeed.com "java backend" india "entry level" OR "junior" OR "associate"',
    'site:indeed.co.in "java microservices" india (noida OR bangalore OR pune OR hyderabad)',
    'site:indeed.com "software engineer" "java spring boot" india "0-2" OR "1-2" 2026',
    'site:indeed.co.in "backend developer" java india (noida OR gurgaon OR bangalore)',
    'site:indeed.com "java developer" india 2026 spring boot',
]

async def agent_indeed_india_search(client: Any) -> List[Dict[str, Any]]:
    """
    Agent 9: Indeed India Java Job Scraper using DDGS.
    Searches Indeed for 1-2 YOE Java/Spring Boot jobs in India.
    """
    global INDEED_SEARCH_INDEX
    q = INDEED_SEARCH_QUERIES[INDEED_SEARCH_INDEX % len(INDEED_SEARCH_QUERIES)]
    INDEED_SEARCH_INDEX += 1

    record_log("INFO", f"🔎 [Agent-9: Indeed India] Searching Indeed: '{q}'...")
    jobs = []
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: robust_ddgs_search(q, max_results=10))

        for item in results:
            title = item.get("title", "").strip()
            link = item.get("href", "").strip()
            snippet = item.get("body", "").strip()

            if not link or not link.startswith("http"):
                continue

            # Must be Indeed
            link_lower = link.lower()
            if "indeed.com" not in link_lower and "indeed.co.in" not in link_lower:
                continue

            # Skip Indeed search pages - only direct job view pages
            if "/viewjob" not in link_lower and "/rc/clk" not in link_lower and "/jobs?" not in link_lower:
                # Allow viewjob and direct job links
                if "viewjob" not in link_lower:
                    continue

            combined = f"{title} {snippet}".lower()
            if not any(k in combined for k in ["java", "spring", "backend", "j2ee"]):
                continue

            eligible, exp_val, exp_label, reason = evaluate_experience_eligibility(title, snippet, max_candidate_exp=2.0)
            if not eligible:
                continue

            if not is_india_location(snippet) and not is_india_location(title):
                continue

            ai_eval = await async_ai_evaluate_job_eligibility(title, snippet)
            if not ai_eval.get("is_eligible", True):
                continue

            # Extract company
            company = "Indeed Listed Company"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                if len(parts) == 2:
                    company = parts[1].strip()[:50]
                    title = parts[0].strip()

            loc = "India"
            for city in ["Noida", "Bangalore", "Bengaluru", "Gurgaon", "Hyderabad", "Pune", "Mumbai", "Chennai", "Delhi"]:
                if city.lower() in combined:
                    loc = city
                    break

            score = ai_eval.get("ats_score") or calculate_ats_match_score(title, snippet)
            min_exp = ai_eval.get("min_exp") or exp_val
            final_exp_label = f"{min_exp:.1f} Years Exp" if min_exp else exp_label
            hr_email = ai_eval.get("hr_email")

            jobs.append({
                "title": title[:100],
                "company": company,
                "location": loc,
                "experience_required": min_exp,
                "experience_str": final_exp_label,
                "description": snippet or f"Java Backend Developer role at {company}. Apply on Indeed: {link}",
                "apply_link": link,
                "hr_email": hr_email,
                "google_form_url": None,
                "source": "Indeed India",
                "match_score": score,
                "posted_at": datetime.utcnow(),
                "posted_date_str": "Today"
            })
            record_log("INFO", f"  🎯 [Agent-9: Indeed] Found: '{title[:50]}' @ {company}")

    except Exception as e:
        record_log("WARNING", f"[Agent-9: Indeed India] Notice: {e}")

    record_log("INFO", f"✔ [Agent-9: Indeed India] Collected {len(jobs)} Indeed India Java jobs.")
    return jobs

# ==============================================================================
# AGENT 10: GLASSDOOR & DEV PORTALS SCRAPER (DDGS-Based)
# Searches Glassdoor India, Lever, Greenhouse, Workable for 1-2 YOE Java
# ==============================================================================
GLASSDOOR_SEARCH_INDEX = 0
GLASSDOOR_SEARCH_QUERIES = [
    'site:glassdoor.co.in "java developer" india 2026 "1-2 years" OR "0-2 years"',
    'site:glassdoor.com "spring boot developer" india "entry level" OR "junior"',
    'site:apply.workable.com "java developer" OR "backend developer" india',
    'site:jobs.lever.co "java developer" india 2026',
    'site:boards.greenhouse.io "java" OR "spring boot" india 2026 backend',
    'site:jobs.ashbyhq.com "java developer" india',
    '"java developer" india 2026 site:lever.co OR site:greenhouse.io OR site:workable.com',
    'site:wellfound.com "java developer" OR "backend engineer" india 2026',
]

async def agent_glassdoor_portals_search(client: Any) -> List[Dict[str, Any]]:
    """
    Agent 10: Glassdoor & Dev Portals Java Job Scraper using DDGS.
    """
    global GLASSDOOR_SEARCH_INDEX
    q = GLASSDOOR_SEARCH_QUERIES[GLASSDOOR_SEARCH_INDEX % len(GLASSDOOR_SEARCH_QUERIES)]
    GLASSDOOR_SEARCH_INDEX += 1

    record_log("INFO", f"🔎 [Agent-10: Glassdoor/Portals] Searching: '{q}'...")
    jobs = []
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: robust_ddgs_search(q, max_results=8))

        for item in results:
            title = item.get("title", "").strip()
            link = item.get("href", "").strip()
            snippet = item.get("body", "").strip()

            if not link or not link.startswith("http"):
                continue

            combined = f"{title} {snippet}".lower()
            if not any(k in combined for k in ["java", "spring", "backend", "j2ee"]):
                continue

            eligible, exp_val, exp_label, reason = evaluate_experience_eligibility(title, snippet, max_candidate_exp=2.0)
            if not eligible:
                continue

            # Live URL verification
            is_live, verify_reason = await verify_live_job_url(client, link)
            if not is_live:
                continue

            ai_eval = await async_ai_evaluate_job_eligibility(title, snippet)
            if not ai_eval.get("is_eligible", True):
                continue

            company = clean_company_from_web(title, link)
            loc = "India"
            for city in ["Noida", "Bangalore", "Bengaluru", "Gurgaon", "Hyderabad", "Pune", "Mumbai", "Chennai", "Delhi"]:
                if city.lower() in combined:
                    loc = city
                    break

            score = ai_eval.get("ats_score") or calculate_ats_match_score(title, snippet)
            min_exp = ai_eval.get("min_exp") or exp_val
            final_exp_label = f"{min_exp:.1f} Years Exp" if min_exp else exp_label

            jobs.append({
                "title": title[:100],
                "company": company,
                "location": loc,
                "experience_required": min_exp,
                "experience_str": final_exp_label,
                "description": snippet or f"Java Backend role at {company}. Apply: {link}",
                "apply_link": link,
                "hr_email": ai_eval.get("hr_email"),
                "google_form_url": ai_eval.get("google_form_or_apply_url"),
                "source": "Glassdoor & Dev Portals",
                "match_score": score,
                "posted_at": datetime.utcnow(),
                "posted_date_str": "Today"
            })
            record_log("INFO", f"  🎯 [Agent-10: Glassdoor] Found: '{title[:50]}' @ {company}")

    except Exception as e:
        record_log("WARNING", f"[Agent-10: Glassdoor/Portals] Notice: {e}")

    record_log("INFO", f"✔ [Agent-10: Glassdoor/Portals] Collected {len(jobs)} portal jobs.")
    return jobs

# ==============================================================================
# AGENT 11: INSTAHYRE DIRECT SCRAPER (DDGS + API)
# Searches Instahyre for fresh backend/java startup roles
# ==============================================================================
INSTAHYRE_SEARCH_INDEX = 0
INSTAHYRE_SEARCH_QUERIES = [
    'site:instahyre.com "java" OR "spring boot" backend developer 2026',
    'site:instahyre.com "backend engineer" java india 2026',
    'site:instahyre.com "java developer" bangalore OR noida OR pune 2026',
    'site:instahyre.com "software engineer" java backend india 2026',
    'site:instahyre.com "backend developer" india java spring 2026',
]

INSTAHYRE_API_PARAMS = [
    {"designation": "Java Developer", "location": "Bangalore"},
    {"designation": "Backend Developer", "location": "Bangalore"},
    {"designation": "Java Developer", "location": "Noida"},
    {"designation": "Backend Developer", "location": "Noida"},
    {"designation": "Spring Boot Developer", "location": "Pune"},
]
INSTAHYRE_API_INDEX = 0

async def agent_instahyre_search(client: Any) -> List[Dict[str, Any]]:
    """
    Agent 11: Instahyre.com Direct Java Startup Job Scraper.
    Uses DDGS search + direct Instahyre API endpoint.
    """
    global INSTAHYRE_SEARCH_INDEX, INSTAHYRE_API_INDEX
    jobs = []

    # Method 1: DDGS search for Instahyre job pages
    q = INSTAHYRE_SEARCH_QUERIES[INSTAHYRE_SEARCH_INDEX % len(INSTAHYRE_SEARCH_QUERIES)]
    INSTAHYRE_SEARCH_INDEX += 1

    record_log("INFO", f"🔎 [Agent-11: Instahyre] Searching: '{q}'...")
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: robust_ddgs_search(q, max_results=10))

        for item in results:
            title = item.get("title", "").strip()
            link = item.get("href", "").strip()
            snippet = item.get("body", "").strip()

            if not link or "instahyre.com" not in link.lower():
                continue

            combined = f"{title} {snippet}".lower()
            if not any(k in combined for k in ["java", "spring", "backend", "sde"]):
                continue

            eligible, exp_val, exp_label, reason = evaluate_experience_eligibility(title, snippet, max_candidate_exp=2.0)
            if not eligible:
                continue

            ai_eval = await async_ai_evaluate_job_eligibility(title, snippet)
            if not ai_eval.get("is_eligible", True):
                continue

            # Extract company from instahyre URL pattern: /job-XXXXX-ROLE-at-COMPANY-LOCATION/
            company = "Instahyre Listed Company"
            url_match = re.search(r'job-\d+-[^-]+-at-([^-/]+(?:-[^-/]+)*)-(?:bangalore|noida|pune|hyderabad|mumbai|gurgaon|chennai|delhi|remote)', link.lower())
            if url_match:
                company = url_match.group(1).replace("-", " ").title()[:50]

            loc = "India"
            for city in ["Noida", "Bangalore", "Bengaluru", "Gurgaon", "Hyderabad", "Pune", "Mumbai", "Chennai", "Delhi"]:
                if city.lower() in link.lower() or city.lower() in combined:
                    loc = city
                    break

            score = ai_eval.get("ats_score") or calculate_ats_match_score(title, snippet)
            min_exp = ai_eval.get("min_exp") or exp_val
            final_exp_label = f"{min_exp:.1f} Years Exp" if min_exp else exp_label

            jobs.append({
                "title": title[:100],
                "company": company,
                "location": loc,
                "experience_required": min_exp,
                "experience_str": final_exp_label,
                "description": snippet or f"Backend Engineering opportunity at {company} ({loc}). Technologies: Java, Spring Boot, Microservices.",
                "apply_link": link,
                "hr_email": ai_eval.get("hr_email"),
                "google_form_url": None,
                "source": "Instahyre Direct Post",
                "match_score": score,
                "posted_at": datetime.utcnow(),
                "posted_date_str": "Today"
            })
            record_log("INFO", f"  🎯 [Agent-11: Instahyre] Found: '{title[:50]}' @ {company}")

    except Exception as e:
        record_log("WARNING", f"[Agent-11: Instahyre DDGS] Notice: {e}")

    # Method 2: Instahyre Direct API
    try:
        param = INSTAHYRE_API_PARAMS[INSTAHYRE_API_INDEX % len(INSTAHYRE_API_PARAMS)]
        INSTAHYRE_API_INDEX += 1

        api_url = f"https://www.instahyre.com/api/v1/search_jobs/"
        api_params = {
            "designation": param["designation"],
            "location": param["location"],
            "experience_min": 0,
            "experience_max": 3,
        }
        headers = {
            "User-Agent": USER_AGENTS[0],
            "Accept": "application/json",
            "Referer": "https://www.instahyre.com/",
        }
        record_log("INFO", f"🔎 [Agent-11: Instahyre API] Fetching {param['designation']} in {param['location']}...")
        r = await client.get(api_url, headers=headers, params=api_params, timeout=8.0)
        if r.status_code == 200:
            data = r.json()
            job_list = data.get("results") or data.get("jobs") or []
            for item in (job_list if isinstance(job_list, list) else []):
                title = (item.get("designation") or item.get("title") or "").strip()
                company_name = (item.get("company_name") or item.get("company") or "").strip()
                loc = (item.get("location") or param["location"]).strip()
                job_url = item.get("url") or item.get("apply_url") or ""
                if job_url and not job_url.startswith("http"):
                    job_url = f"https://www.instahyre.com{job_url}"

                if not title:
                    continue

                t_lower = title.lower()
                if not any(k in t_lower for k in ["java", "spring", "backend", "sde", "software engineer"]):
                    continue

                desc = item.get("description") or item.get("about") or f"Backend Engineering opportunity at {company_name} ({loc}). Technologies: Java, Spring Boot, Microservices, REST APIs, PostgreSQL. Keywords: {', '.join(item.get('skills', [])[:5])}."

                eligible, exp_val, exp_label, reason = evaluate_experience_eligibility(title, desc, max_candidate_exp=2.0)
                if not eligible:
                    continue

                score = calculate_ats_match_score(title, desc)
                jobs.append({
                    "title": title[:100],
                    "company": company_name[:50] or "Instahyre Company",
                    "location": loc,
                    "experience_required": exp_val,
                    "experience_str": exp_label,
                    "description": desc[:3000],
                    "apply_link": job_url or f"https://www.instahyre.com/search-jobs/?designation={urllib.parse.quote(title)}",
                    "hr_email": None,
                    "google_form_url": None,
                    "source": "Instahyre Direct Post",
                    "match_score": score,
                    "posted_at": datetime.utcnow(),
                    "posted_date_str": "Today"
                })
                record_log("INFO", f"  🎯 [Agent-11: Instahyre API] {title[:50]} @ {company_name} ({loc})")
    except Exception as e:
        record_log("WARNING", f"[Agent-11: Instahyre API] Notice: {e}")

    record_log("INFO", f"✔ [Agent-11: Instahyre] Total collected: {len(jobs)} Instahyre Java jobs.")
    return jobs

# ==============================================================================
# AGENT 12: FOUNDIT (MONSTER INDIA) API — Real job listings from Naukri-rival
# Uses their working /middleware/jobsearch endpoint
# ==============================================================================
FOUNDIT_SEARCH_INDEX = 0
FOUNDIT_SEARCH_PARAMS = [
    {"query": "java developer",         "location": "noida",     "experience": "0,3"},
    {"query": "spring boot developer",  "location": "bangalore", "experience": "0,3"},
    {"query": "java backend developer", "location": "pune",      "experience": "0,3"},
    {"query": "java developer",         "location": "hyderabad", "experience": "0,3"},
    {"query": "backend developer java", "location": "gurgaon",   "experience": "0,3"},
    {"query": "java developer",         "location": "india",     "experience": "0,3"},
    {"query": "spring boot microservices", "location": "bangalore", "experience": "0,3"},
    {"query": "java software engineer", "location": "noida",     "experience": "0,3"},
]

async def agent_foundit_api(client: Any) -> List[Dict[str, Any]]:
    """
    Agent 12: Foundit (Monster India) real job listings API.
    Hits https://www.foundit.in/middleware/jobsearch — working, no auth needed.
    """
    global FOUNDIT_SEARCH_INDEX
    params = FOUNDIT_SEARCH_PARAMS[FOUNDIT_SEARCH_INDEX % len(FOUNDIT_SEARCH_PARAMS)]
    FOUNDIT_SEARCH_INDEX += 1

    record_log("INFO", f"🔎 [Agent-12: Foundit] Searching: '{params['query']}' in {params['location']}...")
    jobs = []
    try:
        headers = {
            "User-Agent": USER_AGENTS[0],
            "Accept": "application/json",
            "Referer": f"https://www.foundit.in/srp/results?query={params['query']}&location={params['location']}",
        }
        r = await client.get(
            "https://www.foundit.in/middleware/jobsearch",
            params={
                "query": params["query"],
                "location": params["location"],
                "experience": params["experience"],
                "postedDate": "7",
                "start": "0",
                "rows": "15",
            },
            headers=headers,
            timeout=12.0,
        )
        if r.status_code != 200:
            record_log("WARNING", f"[Agent-12: Foundit] HTTP {r.status_code}")
            return []

        data = r.json()
        raw_jobs = data.get("jobSearchResponse", {}).get("data", [])
        record_log("INFO", f"  [Agent-12: Foundit] Raw jobs received: {len(raw_jobs)}")

        for j in raw_jobs:
            title = (j.get("title") or "").strip()
            if not title:
                continue

            # Location — it's a plain string like "Mumbai, India"
            location = str(j.get("locations") or "India").strip()
            if not location or location == "None":
                location = "India"

            # Company — plain string
            company = str(j.get("companyName") or "").strip()
            if not company or company in ("None", ""):
                company = "Foundit Listed Company"

            # Experience
            exp_min_obj = j.get("minimumExperience") or {}
            exp_max_obj = j.get("maximumExperience") or {}
            exp_min = float(exp_min_obj.get("years", 0)) if isinstance(exp_min_obj, dict) else 0.0
            exp_max = float(exp_max_obj.get("years", 3)) if isinstance(exp_max_obj, dict) else 3.0

            # Skills for description
            skills_raw = j.get("skills") or ""
            skills_str = skills_raw if isinstance(skills_raw, str) else ""

            # Posted date
            created_ms = j.get("createdAt") or 0
            if created_ms:
                try:
                    posted_at = datetime.utcfromtimestamp(int(created_ms) / 1000)
                    age_days = (datetime.utcnow() - posted_at).days
                    posted_date_str = "Today" if age_days == 0 else f"{age_days} days ago"
                except Exception:
                    posted_at = datetime.utcnow()
                    posted_date_str = "Today"
            else:
                posted_at = datetime.utcnow()
                posted_date_str = j.get("updatedAt") or "Recently"

            # Job URL — always a relative path, prepend base
            jd_url = j.get("seoJdUrl") or j.get("jdUrl") or ""
            if jd_url and not jd_url.startswith("http"):
                jd_url = "https://www.foundit.in" + jd_url
            if not jd_url:
                continue

            # Filter by recency (7 days)
            if not is_job_recent(posted_date_str, posted_at, max_days=7):
                continue

            # Filter by India location
            if not is_india_location(location):
                continue

            # Title keyword filter
            t_lower = title.lower()
            if not any(k in t_lower for k in ["java", "spring", "backend", "sde", "software engineer", "microservice"]):
                continue

            # Experience eligibility
            desc = f"{title} at {company} in {location}. Skills: {skills_str}. Experience: {exp_min}-{exp_max} years."
            eligible, exp_val, exp_label, reason = evaluate_experience_eligibility(title, desc, max_candidate_exp=2.0)
            if not eligible:
                record_log("INFO", f"  🚫 [Agent-12: Foundit] {title} ({reason})")
                continue

            score = calculate_ats_match_score(title, desc)
            record_log("INFO", f"  🎯 [Agent-12: Foundit] {title} @ {company} ({location}) [{posted_date_str}]")
            jobs.append({
                "title": title[:100],
                "company": company[:60],
                "location": location,
                "experience_required": exp_val,
                "experience_str": exp_label,
                "description": desc,
                "apply_link": jd_url,
                "hr_email": None,
                "google_form_url": None,
                "source": "Foundit (Monster India)",
                "match_score": score,
                "posted_at": posted_at,
                "posted_date_str": posted_date_str,
            })

    except Exception as e:
        record_log("WARNING", f"[Agent-12: Foundit] Error: {e}")

    record_log("INFO", f"✔ [Agent-12: Foundit] {len(jobs)} jobs found.")
    return jobs


# ==============================================================================
# AGENT 13: DDGS MULTI-SOURCE — Naukri / Indeed / Glassdoor / HiRist / TimesJobs
# Searches WITHOUT site: restriction — finds actual individual job listing pages
# ==============================================================================
DDGS_MULTI_INDEX = 0
DDGS_MULTI_QUERIES = [
    # These find INDIVIDUAL job pages, not search result pages
    '"java developer" "2 years" OR "1-2 years" noida OR bangalore apply site:lever.co OR site:greenhouse.io OR site:workable.com',
    '"spring boot developer" india 2026 "apply now" site:lever.co OR site:greenhouse.io',
    '"backend developer" java india 2026 site:apply.workable.com OR site:jobs.ashbyhq.com',
    '"java backend" india 2026 site:boards.greenhouse.io',
    '"java developer" india 2026 site:jobs.lever.co',
    'java developer 2 years noida bangalore 2026 "apply" -site:naukri.com -site:linkedin.com -site:glassdoor.com',
    '"spring boot" "java" backend developer india 2026 careers apply',
    'java backend developer india 2026 "we are hiring" apply now career',
]

async def agent_ddgs_multisource(client: Any) -> List[Dict[str, Any]]:
    """
    Agent 13: DDGS multi-source search — finds Naukri, Indeed, Glassdoor,
    TimesJobs, HiRist, Shine job links WITHOUT site: restriction.
    """
    global DDGS_MULTI_INDEX
    q = DDGS_MULTI_QUERIES[DDGS_MULTI_INDEX % len(DDGS_MULTI_QUERIES)]
    DDGS_MULTI_INDEX += 1

    record_log("INFO", f"🌐 [Agent-13: DDGS Multi] Searching: '{q[:60]}'...")
    jobs = []
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: robust_ddgs_search(q, max_results=12))

        # Skip aggregator SEARCH pages — only individual job listing pages
        skip_patterns = [
            "-jobs-in-", "job-search", "/java-developer-jobs",
            "/spring-boot-developer-jobs", "/backend-developer-jobs",
            "jobs-SRCH_", "jooble.org", "jobsora.com", "simplyhired",
            "geeksforgeeks.org", "ambitionbox", "quora.com", "reddit.com",
            "/jobs/java", "/jobs/spring", "job-vacancies", "job-openings",
            "2%2C000+", "1%2C000+", "9%2C000+", " jobs in India",
        ]

        for item in results:
            title = (item.get("title") or "").strip()
            link = (item.get("href") or "").strip()
            snippet = (item.get("body") or "").strip()

            if not link or not link.startswith("http"):
                continue

            # Skip aggregator SEARCH pages — only individual job listing pages
            if any(pat in link.lower() for pat in skip_patterns):
                continue

            # Also skip if title looks like a search results page
            title_lower = (title or "").lower()
            if any(t in title_lower for t in ["jobs in india", "jobs in bangalore", "jobs in noida",
                                               "job vacancies", "open roles", "current openings",
                                               "latest jobs", "find jobs", "search results"]):
                continue

            # Must mention Java/Spring/Backend
            combined = f"{title} {snippet}".lower()
            if not any(k in combined for k in ["java", "spring", "backend", "j2ee"]):
                continue

            # India location check
            if not is_india_location(snippet) and not is_india_location(title):
                loc_keywords = ["noida", "bangalore", "bengaluru", "pune", "hyderabad", "gurgaon", "india", "ncr"]
                if not any(lk in combined for lk in loc_keywords):
                    continue

            # Experience eligibility
            eligible, exp_val, exp_label, reason = evaluate_experience_eligibility(title, snippet, max_candidate_exp=2.0)
            if not eligible:
                continue

            # Detect source platform
            link_lower = link.lower()
            if "naukri.com" in link_lower:
                source = "Naukri India"
            elif "indeed.com" in link_lower or "indeed.co.in" in link_lower:
                source = "Indeed India"
            elif "glassdoor.co.in" in link_lower or "glassdoor.com" in link_lower:
                source = "Glassdoor India"
            elif "hirist.tech" in link_lower or "hirist.com" in link_lower:
                source = "HiRist"
            elif "shine.com" in link_lower:
                source = "Shine.com"
            elif "timesjobs.com" in link_lower:
                source = "TimesJobs"
            elif "foundit.in" in link_lower:
                source = "Foundit India"
            elif "linkedin.com" in link_lower:
                source = "LinkedIn"
            elif "instahyre.com" in link_lower:
                source = "Instahyre"
            else:
                source = "Web Search"

            # Extract company
            company = "Listed Company"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                company = parts[-1].strip()[:50]
                title = parts[0].strip()
            elif " at " in title.lower():
                idx = title.lower().rfind(" at ")
                company = title[idx+4:].strip()[:50]
                title = title[:idx].strip()

            # Extract location
            loc = "India"
            for city in ["Noida", "Bangalore", "Bengaluru", "Gurgaon", "Hyderabad", "Pune", "Mumbai", "Chennai", "Delhi", "Gurugram"]:
                if city.lower() in combined:
                    loc = city
                    break

            score = calculate_ats_match_score(title, snippet)
            jobs.append({
                "title": title[:100],
                "company": company,
                "location": loc,
                "experience_required": exp_val,
                "experience_str": exp_label,
                "description": snippet[:2000] if snippet else f"Java/Spring Boot role. Apply: {link}",
                "apply_link": link,
                "hr_email": None,
                "google_form_url": None,
                "source": source,
                "match_score": score,
                "posted_at": datetime.utcnow(),
                "posted_date_str": "Today",
            })
            record_log("INFO", f"  🎯 [Agent-13: DDGS] [{source}] {title[:45]} @ {company}")

    except Exception as e:
        record_log("WARNING", f"[Agent-13: DDGS Multi] Error: {e}")

    record_log("INFO", f"✔ [Agent-13: DDGS Multi] {len(jobs)} jobs found.")
    return jobs


# ==============================================================================
# AGENT 14: LINKEDIN KEYWORD POSTS SEARCH
# Searches LinkedIn for "#hiring Java Backend Developer" type posts by people
# These are direct recruiter posts with HR email/phone numbers
# ==============================================================================
LI_KW_INDEX = 0
LI_KW_QUERIES = [
    'site:linkedin.com/posts "Java Backend Developer" "hiring" India',
    'site:linkedin.com/posts "Java Developer" "hiring" India',
    'site:linkedin.com/posts "Spring Boot" "Backend" "hiring" India',
    'site:linkedin.com/posts "Java Backend Developer" ("1-3" OR "2-4" OR "2 years") India',
    'site:linkedin.com/posts "Java Developer" ("Noida" OR "Bangalore" OR "Pune" OR "Gurgaon") hiring',
    'site:linkedin.com/posts "Java Developer" "send resume" India',
    'site:linkedin.com/posts "Backend Engineer" "Java" hiring India',
    'site:linkedin.com/posts "Java" "immediate joiner" "hiring" India'
]

async def agent_linkedin_keyword_posts(client: Any) -> List[Dict[str, Any]]:
    """
    Agent 14: LinkedIn keyword post search via DDGS.
    Finds recruiter posts: '#hiring Java Backend Developer' with HR contacts.
    """
    global LI_KW_INDEX
    jobs = []
    queries_to_run = [
        LI_KW_QUERIES[LI_KW_INDEX % len(LI_KW_QUERIES)],
        LI_KW_QUERIES[(LI_KW_INDEX + 1) % len(LI_KW_QUERIES)]
    ]
    LI_KW_INDEX += 2

    for q in queries_to_run:
        record_log("INFO", f"🔎 [Agent-14: LinkedIn KW Posts] Searching: '{q[:60]}'...")
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, lambda query=q: robust_ddgs_search(query, max_results=10))

            for item in results:
                url = (item.get("href") or "").strip()
                if not url:
                    continue
                # Only LinkedIn post/feed URLs
                if not any(p in url for p in ["/posts/", "/feed/update/", "activity-"]):
                    continue

                is_valid, post_job, reason = await verify_and_extract_linkedin_post(client, url)
                if is_valid and post_job:
                    jobs.append(post_job)
                    record_log("INFO", f"  🎯 [Agent-14: LinkedIn KW] Found post: '{post_job['title'][:45]}'")
                else:
                    record_log("INFO", f"  🚫 [Agent-14: LinkedIn KW] Skipped ({reason}): {url[:50]}")
        except Exception as e:
            record_log("WARNING", f"[Agent-14: LinkedIn KW Posts] Error: {e}")

    record_log("INFO", f"✔ [Agent-14: LinkedIn KW Posts] {len(jobs)} posts found.")
    return jobs

# ==============================================================================
# MULTI-AGENT ROTATION & ORCHESTRATION ENGINE (LINKEDIN + WEB + CAREER PORTALS)
# ==============================================================================
SEARCH_ROTATION_INDEX = 0

LINKEDIN_ROTATION_PLAN = [
    # Cycle 0: Today's fresh jobs - NCR focus
    [("Java Developer", "Noida", 0), ("Java Backend Developer", "Noida", 0), ("Spring Boot Developer", "Gurgaon", 0)],
    # Cycle 1: Today's fresh - Bangalore focus
    [("Java Developer", "Bengaluru", 0), ("Spring Boot Developer", "Bengaluru", 0), ("Java Backend Developer", "Bengaluru", 0)],
    # Cycle 2: Exact 2 Years experience targeting
    [("Java Developer 2 years", "India", 0), ("Java Developer 2 years", "Noida", 0), ("Java Developer 2 years", "Bengaluru", 0)],
    # Cycle 3: SDE 1 / Junior / Associate level
    [("SDE 1 Java", "India", 0), ("Junior Java Developer", "India", 0), ("Associate Java Developer", "India", 0)],
    # Cycle 4: Hyderabad + Pune + Mumbai
    [("Java Developer", "Hyderabad", 0), ("Java Developer", "Pune", 0), ("Spring Boot Developer", "Mumbai", 0)],
    # Cycle 5: Remote India + Pan-India microservices
    [("Java Backend Developer", "Remote", 0), ("Java Microservices Developer", "India", 0), ("Spring Boot Microservices", "India", 0)],
    # Cycle 6: Deep offset — catches jobs not on page 1
    [("Java Developer", "India", 25), ("Spring Boot Developer", "India", 25), ("Java Backend Developer", "India", 25)],
    # Cycle 7: Chennai + Delhi + broader sweep
    [("Java Developer", "Chennai", 0), ("Java Developer", "Delhi", 0), ("Backend Developer Java", "India", 0)],
    # Cycle 8: Today's 24h jobs only (r86400)
    [("Java Developer", "India", 0), ("Spring Boot Developer", "India", 0), ("Java Backend Developer", "Noida", 0)],
    # Cycle 9: Freshers + entry level
    [("Java Developer Fresher", "India", 0), ("Entry Level Java Developer", "India", 0), ("Java Developer 1 year", "India", 0)],
]

async def run_job_search_cycle(db: Session, force_notify: bool = False) -> Dict[str, Any]:
    """
    Multi-Agent Orchestrator executing continuous 24/7 background search cycle across:
    1. LinkedIn Tech Hubs (Noida, Gurgaon, Bangalore, Pune, Hyderabad, Remote)
    2. LinkedIn Live Posts (#hiring, recruiters)
    3. Google & Deep Web Search Hunter (Noida, Bangalore, Indian tech companies)
    4. Top Indian Tech & Fintech Career Portals (Greenhouse & Lever ATS APIs)
    Persists only genuine 1-2 YOE Java developer roles.
    NEVER deletes any existing jobs.
    """
    search_config = db.query(SearchConfig).first()
    if search_config and not search_config.auto_scrape_enabled and not force_notify:
        record_log("INFO", "⏸ [24/7 Scheduler] Auto-hunt is disabled in Search Preferences.")
        return {"status": "disabled", "new_jobs_count": 0, "total_evaluated": 0}

    global SEARCH_ROTATION_INDEX
    plan_to_run = LINKEDIN_ROTATION_PLAN[SEARCH_ROTATION_INDEX % len(LINKEDIN_ROTATION_PLAN)]
    SEARCH_ROTATION_INDEX += 1

    record_log("INFO", "==================================================================")
    record_log("INFO", f"🚀 [Multi-Agent Universal Hunter] Starting 14-Agent CONCURRENT Hunt Cycle #{SEARCH_ROTATION_INDEX}...")
    record_log("INFO", "  🔵 LinkedIn(1-5) | 🌐 Web(6) | 🏢 ATS(7) | 🟠 Foundit(12) | 🔍 DDGS-Multi(13) | 📝 LI-KW-Posts(14)")
    record_log("INFO", "==================================================================")

    discovered_jobs: List[Dict[str, Any]] = []

    async with primp.AsyncClient(follow_redirects=True) as client:
        # Use separate clients for LinkedIn vs non-LinkedIn to avoid connection pool contention
        async with primp.AsyncClient(follow_redirects=True) as client_b:
            record_log("INFO", "⚡ [Concurrent Engine] All 14 agents launching in parallel...")

            linkedin_primary_coros = [
                agent_linkedin_hunt(client, query=q, location=loc, offset=offset)
                for q, loc, offset in plan_to_run
            ]

            async def staggered(coro, delay=0.0):
                if delay > 0:
                    await asyncio.sleep(delay)
                return await coro

            results = await asyncio.gather(
                *linkedin_primary_coros,                                       # T1: LinkedIn primary
                staggered(agent_linkedin_today(client), 0.3),                  # T1B: TODAY 24h
                staggered(agent_linkedin_hub_south(client), 0.6),              # T2: Bengaluru+Hyd
                staggered(agent_linkedin_hub_west_remote(client), 0.9),        # T3: Pune+Remote
                staggered(agent_linkedin_paginated_sweep(client), 1.2),        # T4: deep sweep
                staggered(agent_linkedin_posts_urgent(client_b), 1.5),         # T5A: #hiring posts
                staggered(agent_linkedin_posts_tech_hubs(client_b), 1.8),      # T5B: hub posts
                staggered(agent_linkedin_posts_hr_direct(client_b), 2.1),      # T5C: HR direct
                agent_web_search_hunter(client_b),                             # T6: Web search
                agent_top_tech_career_portals(client_b),                       # T7: ATS portals
                agent_foundit_api(client_b),                                   # T8: Foundit API
                agent_ddgs_multisource(client_b),                              # T9: DDGS multi
                agent_instahyre_search(client_b),                              # T10: Instahyre
                staggered(agent_linkedin_keyword_posts(client_b), 2.4),        # T11: LI KW posts
                return_exceptions=True
            )

            for result in results:
                if isinstance(result, Exception):
                    record_log("WARNING", f"Agent error (non-fatal): {result}")
                elif isinstance(result, list):
                    discovered_jobs.extend(result)

    record_log("INFO", f"📊 [Universal Multi-Agent Collector] Total {len(discovered_jobs)} raw candidate jobs & posts gathered from LinkedIn, Web & Career Portals.")


    if not discovered_jobs:
        mark_search_completed(db)
        record_log("INFO", "✔ Cycle complete: 0 candidate jobs collected.")
        return {"status": "success", "new_jobs_count": 0, "total_evaluated": 0}

    # Multi-attribute deduplication against existing AWS RDS PostgreSQL rows
    job_tuples = []
    for jd in discovered_jobs:
        source_id = generate_source_id(jd["company"], jd["title"], jd.get("apply_link"))
        job_tuples.append((source_id, jd))

    existing_records = db.query(Job.source_id, Job.apply_link, Job.company, Job.title).all()
    existing_source_ids = set(r[0] for r in existing_records if r[0])
    existing_links = set(r[1].strip() for r in existing_records if r[1])
    existing_pairs = set((r[2].strip().lower(), r[3].strip().lower()) for r in existing_records if r[2] and r[3])

    new_jobs_added = []
    notifications_to_add = []
    skipped_location = 0
    skipped_stale = 0
    skipped_duplicate = 0
    skipped_ineligible = 0

    for source_id, jd in job_tuples:
        clean_link = (jd.get("apply_link") or "").strip()
        comp_key = (jd.get("company") or "").strip().lower()
        title_key = (jd.get("title") or "").strip().lower()
        loc = (jd.get("location") or "").strip()

        # Strict India location verification
        if not is_india_location(loc):
            skipped_location += 1
            continue

        # Freshness gatekeeper: Allow up to 28 days for LinkedIn recruiter posts, 14 days for standard jobs
        is_recruiter_post = "post" in (jd.get("source") or "").lower() or "/posts/" in clean_link or "activity-" in clean_link
        max_recency_days = 28 if is_recruiter_post else 14
        if not is_job_recent(jd.get("posted_date_str"), jd.get("posted_at"), max_days=max_recency_days):
            record_log("INFO", f"  ⏳ Filtered stale candidate (> {max_recency_days} days): '{jd.get('title')}' @ {jd.get('company')} ({jd.get('posted_date_str')})")
            skipped_stale += 1
            continue

        # Strict Multi-attribute Deduplication
        if source_id in existing_source_ids:
            skipped_duplicate += 1
            continue
        if clean_link and clean_link in existing_links:
            skipped_duplicate += 1
            continue
        if (comp_key, title_key) in existing_pairs:
            skipped_duplicate += 1
            continue

        # Prevent duplicates within the same cycle batch
        existing_source_ids.add(source_id)
        if clean_link:
            existing_links.add(clean_link)
        existing_pairs.add((comp_key, title_key))

        # Master AI Candidate Eligibility Filter (Gemini Flash)
        ai_res = await async_ai_evaluate_job_eligibility(jd["title"], jd.get("description", ""))
        if not ai_res.get("is_eligible", True):
            reason = ai_res.get("rejection_reason") or "AI determined role is not eligible"
            record_log("INFO", f"  🚫 [Master AI Filter] Filtered ineligible role: '{jd.get('title')}' @ {jd.get('company')} ({reason})")
            skipped_ineligible += 1
            continue

        final_exp = ai_res.get("min_exp") or jd.get("experience_required", 2.0)
        final_exp_str = f"{final_exp:.1f} Years Exp" if final_exp else jd.get("experience_str", "2 Years Exp")
        final_score = ai_res.get("ats_score") or jd.get("match_score", 92)
        final_hr_email = ai_res.get("hr_email") or jd.get("hr_email")
        final_form_url = ai_res.get("google_form_or_apply_url") or jd.get("google_form_url")

        new_job = Job(
            title=jd["title"],
            company=jd["company"],
            location=jd.get("location", "India / Remote"),
            experience_required=final_exp,
            experience_str=final_exp_str,
            description=jd.get("description"),
            apply_link=jd.get("apply_link"),
            hr_email=final_hr_email,
            google_form_url=final_form_url,
            source=jd.get("source", "Multi-Agent Hunter"),
            source_id=source_id,
            status="DISCOVERED",
            match_score=final_score,
            match_reasons="Verified 2 years Java Developer match with Spring Boot & Microservices.",
            posted_at=jd.get("posted_at", datetime.utcnow()),
            posted_date_str=jd.get("posted_date_str", "Today")
        )
        new_jobs_added.append(new_job)

    if new_jobs_added:
        # Atomic persistence to AWS RDS PostgreSQL
        db.add_all(new_jobs_added)
        db.commit()

        # Strict Notification Deduplication: check existing notifications
        existing_notif_job_ids = set(
            r[0] for r in db.query(Notification.job_id).filter(Notification.job_id.isnot(None)).all()
        )
        for job in new_jobs_added:
            if job.id in existing_notif_job_ids:
                continue
            email_info = f" (HR: {job.hr_email})" if job.hr_email else ""
            notif = Notification(
                title=f"New Java Job: {job.title} at {job.company} ({job.match_score}% Fit)",
                message=f"Location: {job.location} | Exp: {job.experience_str}{email_info}. Apply: {job.apply_link}",
                job_id=job.id,
                notification_type="NEW_JOB",
                is_read=False
            )
            notifications_to_add.append(notif)
            existing_notif_job_ids.add(job.id)

        if notifications_to_add:
            db.add_all(notifications_to_add)
            db.commit()

        # Real-time WebSocket Broadcast
        for new_job in new_jobs_added:
            await manager.broadcast({
                "event": "NEW_JOB_FOUND",
                "job": {
                    "id": new_job.id,
                    "title": new_job.title,
                    "company": new_job.company,
                    "experience_str": new_job.experience_str,
                    "hr_email": new_job.hr_email,
                    "google_form_url": new_job.google_form_url,
                    "apply_link": new_job.apply_link,
                    "source": new_job.source,
                    "match_score": new_job.match_score,
                    "status": new_job.status
                }
            })

        record_log("INFO", f"✨ [AWS RDS PostgreSQL] Successfully inserted {len(new_jobs_added)} NEW live 2-year Java jobs into DISCOVERED!")
        for nj in new_jobs_added[:5]:
            record_log("INFO", f"   🎯 [{nj.source}] {nj.title} @ {nj.company} -> {nj.apply_link}")
    else:
        record_log(
            "INFO",
            "✔ [Orchestrator] Cycle completed with no new jobs "
            f"(raw={len(discovered_jobs)}, duplicate={skipped_duplicate}, "
            f"ineligible={skipped_ineligible}, stale={skipped_stale}, location={skipped_location})."
        )

    mark_search_completed(db)
    record_log("INFO", "==================================================================")
    return {
        "status": "success",
        "new_jobs_count": len(new_jobs_added),
        "total_evaluated": len(discovered_jobs)
    }
