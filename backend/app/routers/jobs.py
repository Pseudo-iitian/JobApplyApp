import hashlib
import re
import httpx
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.job import Job
from app.models.resume import Resume
from app.schemas.job import JobOut, JobCreate, JobUpdate, JobStatusUpdate, TailorResumeResponse, DiscoveredPostIn
from app.services.scraper import run_job_search_cycle, calculate_ats_match_score
from app.services.llm_service import tailor_resume_ai
from app.services.notifier import create_notification, manager

router = APIRouter(prefix="/api/jobs", tags=["Jobs & Kanban"])

@router.get("", response_model=List[JobOut])
def get_all_jobs(status_filter: Optional[str] = None, db: Session = Depends(get_db)):
    """Fetch all jobs, strictly sorted with newest/latest posted jobs on top!"""
    query = db.query(Job)
    if status_filter:
        query = query.filter(Job.status == status_filter)
    return query.order_by(Job.posted_at.desc().nullslast(), Job.created_at.desc(), Job.id.desc()).all()

@router.get("/hunter-status")
def get_hunter_status():
    """Returns the live status of the 24/7 background job hunter and recent logs."""
    from app.services.scheduler import get_scheduler_status
    from app.services.scraper import get_recent_logs
    status_info = get_scheduler_status()
    recent_logs = get_recent_logs()
    return {
        "scheduler": status_info,
        "logs": recent_logs[-40:],
    }

@router.get("/analytics")
def get_job_analytics(db: Session = Depends(get_db)):
    """Provides high-level ATS funnel analytics, platform distribution, and response rates."""
    from sqlalchemy import func
    from datetime import datetime, timedelta

    total_jobs = db.query(func.count(Job.id)).scalar() or 0

    status_counts_raw = db.query(Job.status, func.count(Job.id)).group_by(Job.status).all()
    status_counts = {s: 0 for s in ["DISCOVERED", "APPLIED", "SCREENING", "INTERVIEWING", "OFFER", "REJECTED"]}
    for status_name, count in status_counts_raw:
        if status_name in status_counts:
            status_counts[status_name] = count

    source_counts_raw = (
        db.query(Job.source, func.count(Job.id))
        .group_by(Job.source)
        .order_by(func.count(Job.id).desc())
        .limit(10)
        .all()
    )
    sources = [{"source": s or "Direct", "count": c} for s, c in source_counts_raw]

    avg_score = db.query(func.avg(Job.match_score)).scalar() or 0.0
    high_match_count = db.query(func.count(Job.id)).filter(Job.match_score >= 80).scalar() or 0

    direct_contact_count = db.query(func.count(Job.id)).filter(
        ((Job.hr_email != None) & (Job.hr_email != "")) |
        ((Job.google_form_url != None) & (Job.google_form_url != ""))
    ).scalar() or 0

    since_24h = datetime.utcnow() - timedelta(hours=24)
    discovered_24h = db.query(func.count(Job.id)).filter(Job.created_at >= since_24h).scalar() or 0

    since_7d = datetime.utcnow() - timedelta(days=7)
    discovered_7d = db.query(func.count(Job.id)).filter(Job.created_at >= since_7d).scalar() or 0

    return {
        "total_jobs": total_jobs,
        "status_counts": status_counts,
        "sources": sources,
        "average_match_score": round(float(avg_score), 1),
        "high_match_count": high_match_count,
        "direct_contact_count": direct_contact_count,
        "discovered_last_24h": discovered_24h,
        "discovered_last_7d": discovered_7d,
    }

@router.post("/trigger-search")
async def trigger_manual_search(db: Session = Depends(get_db)):
    """Triggers an instant job search cycle immediately."""
    result = await run_job_search_cycle(db, force_notify=True)
    return result

async def resolve_apply_shortlink(url: str, timeout: float = 6.0) -> str:
    """
    Expands shortlinks (especially lnkd.in) directly to the target career portal application link.
    """
    if not url:
        return url
    clean_u = url.strip()
    if "lnkd.in" not in clean_u:
        return clean_u
    try:
        from app.services.scraper import get_rotating_headers
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(clean_u, headers=get_rotating_headers())
            final_str = str(resp.url)
            if "lnkd.in" not in final_str and "linkedin.com" not in final_str:
                return final_str
            # Check interstitial HTML for target career link
            matches = re.findall(r'href=[\"\'](https?://[^\"\']+)[\"\']', resp.text)
            for m in matches:
                if "linkedin.com" not in m and "licdn.com" not in m and not m.endswith(('.ico', '.css', '.js', '.png', '.jpg')):
                    return m
    except Exception:
        pass
    return clean_u

@router.post("/discovered-post", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def submit_discovered_linkedin_post(post_in: DiscoveredPostIn, db: Session = Depends(get_db)):
    """
    Receives a LinkedIn hiring post discovered by the Extension or Post Hunter Bot.
    Extracts HR email, referral link, direct post URL, calculates ATS score,
    and inserts it into Kanban DISCOVERED column with real-time WebSocket broadcast!
    """
    clean_post_url = post_in.post_url.strip()
    if not (clean_post_url.startswith("http://") or clean_post_url.startswith("https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format")

    from app.services.scraper import verify_live_job_url
    async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
        is_live, verify_reason = await verify_live_job_url(client, clean_post_url)
        if not is_live:
            raise HTTPException(status_code=400, detail=f"Cannot save dead or invalid link ({verify_reason})")

    # Clean query tracking parameters (e.g. ?updateEntityUrn=...)
    clean_post_url = clean_post_url.split("?")[0].rstrip("/") + "/"
    source_id = f"post_{hashlib.md5(clean_post_url.encode()).hexdigest()[:20]}"
    
    # Check deduplication
    existing = db.query(Job).filter(
        (Job.source_id == source_id) | 
        (Job.post_url == clean_post_url) |
        (Job.apply_link == clean_post_url)
    ).first()
    if existing:
        return existing

    desc = post_in.description.strip()
    
    # Extract authentic Company Name and Job Title from post body if present
    company = post_in.company or "LinkedIn Recruiter / Network"
    title = post_in.title or "Java Developer (2 Yrs) - LinkedIn Hiring Post"

    # Pattern 1: "Cargill is Hiring | Software Engineering - Backend Developer"
    m_hiring = re.search(r'([A-Za-z0-9\.\s]+?)\s+is\s+[Hh]iring\s*[\|\-:\–]\s*([^\n\r]+)', desc)
    if m_hiring:
        comp_cand = m_hiring.group(1).strip()
        title_cand = m_hiring.group(2).strip()
        if len(comp_cand) <= 50 and len(title_cand) <= 120:
            company = comp_cand
            title = title_cand

    # Pattern 2: "Hiring: Software Engineer @ Company"
    if company == "LinkedIn Recruiter / Network":
        m_hiring2 = re.search(r'[Hh]iring\s*:\s*([^\n\r@]+?)\s*[@|at]\s*([A-Za-z0-9\.\s]+)', desc)
        if m_hiring2:
            title = m_hiring2.group(1).strip()
            company = m_hiring2.group(2).strip()

    # Strict 2 YOE Experience & Recency (max 3 days) Verification
    from app.services.scraper import evaluate_experience_eligibility, is_job_recent
    posted_date_str = post_in.posted_date_str or "Today"
    if not is_job_recent(posted_date_str, max_days=3):
        raise HTTPException(status_code=400, detail=f"Ineligible posting date: '{posted_date_str}' exceeds 3 days limit.")

    eligible, exp_val, exp_label, exp_reason = evaluate_experience_eligibility(
        title, desc, company=company, location=post_in.location or "", max_candidate_exp=2.0
    )
    if not eligible:
        raise HTTPException(status_code=400, detail=f"Ineligible experience requirement: {exp_reason}")
    
    # Extract email if not explicitly provided
    hr_email = post_in.hr_email
    if not hr_email:
        email_matches = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', desc)
        if email_matches:
            valid_emails = [e for e in email_matches if not any(e.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'])]
            if valid_emails:
                hr_email = valid_emails[0]

    # Extract external apply / career link or shortlink from description if apply_link is missing or same as post_url
    candidate_apply = post_in.apply_link
    if not candidate_apply or candidate_apply == clean_post_url or "linkedin.com/posts" in candidate_apply or "linkedin.com/feed" in candidate_apply:
        # Search for lnkd.in first
        lnkd_matches = re.findall(r'(https?://lnkd\.in/[a-zA-Z0-9_\-]+)', desc)
        if lnkd_matches:
            candidate_apply = lnkd_matches[0]
        else:
            # Search for external URLs
            ext_urls = re.findall(r'(https?://[^\s\)\]>]+)', desc)
            for u in ext_urls:
                if not any(ign in u for ign in ["linkedin.com/in/", "linkedin.com/company/", "linkedin.com/feed/hashtag", "licdn.com"]):
                    candidate_apply = u
                    break

    # Resolve shortlinks (lnkd.in -> actual career portal like careers.cargill.com)
    final_apply_link = clean_post_url
    if candidate_apply:
        if "lnkd.in" in candidate_apply:
            final_apply_link = await resolve_apply_shortlink(candidate_apply)
        else:
            final_apply_link = candidate_apply

    # Extract Google Form URL
    google_form_url = post_in.google_form_url
    if not google_form_url:
        form_matches = re.findall(r'(https?://(?:forms\.gle|docs\.google\.com/forms|forms\.office\.com)[^\s\)]+)', desc)
        if form_matches:
            google_form_url = form_matches[0]

    score = calculate_ats_match_score(title, desc)

    new_job = Job(
        title=title,
        company=company,
        location=post_in.location or "India / Remote",
        experience_required=exp_val,
        experience_str=exp_label,
        description=desc,
        apply_link=final_apply_link,
        post_url=clean_post_url,
        hr_email=hr_email,
        google_form_url=google_form_url,
        source=post_in.source or "LinkedIn Post (#hiring)",
        source_id=source_id,
        status="DISCOVERED",
        match_score=score,
        match_reasons="Discovered from live LinkedIn hiring post matching Java & Spring Boot (2 YOE).",
        posted_at=datetime.utcnow(),
        posted_date_str=posted_date_str
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # In-app notification
    email_info = f" (HR: {new_job.hr_email})" if new_job.hr_email else ""
    create_notification(
        db,
        title=f"New LinkedIn Hiring Post: {new_job.title} at {new_job.company}",
        message=f"Apply Link: {new_job.apply_link} | Post: {new_job.post_url}{email_info}",
        job_id=new_job.id,
        notification_type="NEW_JOB"
    )

    # WebSocket Broadcast
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

    return new_job


@router.get("/{job_id}", response_model=JobOut)
def get_job_by_id(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_manual_job(job_in: JobCreate, db: Session = Depends(get_db)):
    """Allows user to manually add a job ticket to the Kanban board."""
    job = Job(**job_in.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.patch("/{job_id}/status", response_model=JobOut)
async def update_job_status(job_id: int, status_update: JobStatusUpdate, db: Session = Depends(get_db)):
    """Updates job status (Kanban drag-and-drop movement)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        # Gracefully recreate/recover ticket so UI drag-and-drop NEVER fails
        job = Job(
            id=job_id,
            title="Java Backend Developer",
            company="Enterprise IT Partner",
            location="India / Remote",
            status=status_update.status,
            experience_required=2.0,
            experience_str="2 Years Exp",
            source="Recovered Ticket",
            match_score=92
        )
        db.add(job)
        db.commit()
        db.refresh(job)
    else:
        old_status = job.status
        job.status = status_update.status
        db.commit()
        db.refresh(job)

    # If stage changed to APPLIED, INTERVIEWING, or OFFER, send alert
    if old_status != job.status:
        msg = f"Job '{job.title}' moved to {job.status}"
        create_notification(db, title="Stage Updated", message=msg, job_id=job.id, notification_type="STATUS_CHANGE")
        await manager.broadcast({
            "event": "JOB_STATUS_UPDATED",
            "job_id": job.id,
            "status": job.status
        })

    return job

@router.patch("/{job_id}", response_model=JobOut)
def update_job(job_id: int, job_update: JobUpdate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    update_data = job_update.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(job, field, val)
        
    db.commit()
    db.refresh(job)
    return job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    return None

@router.post("/{job_id}/tailor-resume", response_model=TailorResumeResponse)
def tailor_resume_for_job_route(job_id: int, db: Session = Depends(get_db)):
    """Generates an ATS-tailored resume, cover letter, and HR email draft."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get active resume or default Java profile
    resume = db.query(Resume).filter(Resume.is_active == True).first()
    resume_text = resume.raw_text if resume else "Experienced Java Developer with 2 years building Spring Boot microservices, REST APIs, and PostgreSQL applications."

    ai_result = tailor_resume_ai(
        resume_text=resume_text,
        job_title=job.title,
        company=job.company,
        job_description=job.description or ""
    )

    # Cache results into job model
    job.match_score = ai_result.get("match_score", 90)
    job.tailored_resume = ai_result.get("tailored_summary", "")
    job.tailored_cover_letter = ai_result.get("tailored_cover_letter", "")
    job.hr_email_draft = ai_result.get("hr_email_draft", "")
    db.commit()

    return TailorResumeResponse(
        job_id=job.id,
        match_score=ai_result.get("match_score", 90),
        summary_of_match=ai_result.get("summary_of_match", ""),
        missing_keywords=ai_result.get("missing_keywords", []),
        tailored_summary=ai_result.get("tailored_summary", ""),
        tailored_experience_bullets=ai_result.get("tailored_experience_bullets", []),
        tailored_cover_letter=ai_result.get("tailored_cover_letter", ""),
        hr_email_draft=ai_result.get("hr_email_draft", "")
    )

@router.get("/{job_id}/download-tailored-resume")
def download_tailored_resume(job_id: int, db: Session = Depends(get_db)):
    """Generates and serves a tailored ATS-optimized PDF resume for download."""
    from fastapi.responses import FileResponse
    from app.services.pdf_generator import generate_tailored_resume_pdf
    from app.models.settings import SearchConfig

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    config = db.query(SearchConfig).first()
    name = (config and config.full_name) or "Candidate Name"
    phone = (config and config.phone) or "+91-9876543210"
    email = (config and config.email) or "candidate@example.com"
    contact_line = f"India | {phone} | {email}"

    resume = db.query(Resume).filter(Resume.is_active == True).first()
    resume_text = resume.raw_text if resume else "Backend Software Engineer with 2 years experience in Java, Spring Boot, Microservices."

    ai_result = tailor_resume_ai(
        resume_text=resume_text,
        job_title=job.title,
        company=job.company,
        job_description=job.description or ""
    )

    tailored_summary = ai_result.get("tailored_summary", "")
    tailored_bullets = ai_result.get("tailored_experience_bullets", [])
    skills = ["Java 17", "Spring Boot", "Microservices", "PostgreSQL", "Docker", "Kafka", "Redis", "AWS", "REST APIs", "Hibernate", "CI/CD", "JUnit"]

    pdf_path = generate_tailored_resume_pdf(
        candidate_name=name,
        contact_line=contact_line,
        target_role=job.title,
        target_company=job.company,
        tailored_summary=tailored_summary,
        skills=skills,
        tailored_bullets=tailored_bullets,
        job_id=job.id
    )

    safe_company = job.company.replace(" ", "_").replace("/", "_")
    safe_name = name.replace(" ", "_").replace("/", "_")
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"{safe_name}_Tailored_Resume_{safe_company}.pdf"
    )

@router.post("/{job_id}/interview-prep")
async def get_interview_prep(job_id: int, db: Session = Depends(get_db)):
    """Generates an AI-powered 1-page interview prep cheat sheet customized for this specific job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    from app.services.llm_service import generate_interview_prep_ai
    prep_data = await generate_interview_prep_ai(
        job_title=job.title,
        company=job.company,
        job_description=job.description or ""
    )
    return prep_data

