from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class JobBase(BaseModel):
    title: str
    company: str
    location: Optional[str] = "Remote / Flexible"
    experience_required: Optional[float] = 2.0
    experience_str: Optional[str] = "2 Years"
    description: Optional[str] = None
    apply_link: Optional[str] = None
    post_url: Optional[str] = None
    hr_email: Optional[str] = None
    google_form_url: Optional[str] = None
    source: Optional[str] = "Online Scraper"
    status: Optional[str] = "DISCOVERED"
    match_score: Optional[int] = 85
    match_reasons: Optional[str] = None
    notes: Optional[str] = None
    posted_at: Optional[datetime] = None
    posted_date_str: Optional[str] = "Recently"

class JobCreate(JobBase):
    source_id: Optional[str] = None

class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    experience_required: Optional[float] = None
    description: Optional[str] = None
    apply_link: Optional[str] = None
    post_url: Optional[str] = None
    hr_email: Optional[str] = None
    google_form_url: Optional[str] = None
    status: Optional[str] = None
    match_score: Optional[int] = None
    notes: Optional[str] = None
    tailored_resume: Optional[str] = None
    tailored_cover_letter: Optional[str] = None
    hr_email_draft: Optional[str] = None

class JobStatusUpdate(BaseModel):
    status: str  # DISCOVERED, APPLIED, SCREENING, INTERVIEWING, OFFER, REJECTED

class JobOut(JobBase):
    id: int
    source_id: Optional[str] = None
    tailored_resume: Optional[str] = None
    tailored_cover_letter: Optional[str] = None
    hr_email_draft: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TailorResumeResponse(BaseModel):
    job_id: int
    match_score: int
    summary_of_match: str
    missing_keywords: List[str]
    tailored_summary: str
    tailored_experience_bullets: List[str]
    tailored_cover_letter: str
    hr_email_draft: str

class DiscoveredPostIn(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = "LinkedIn Recruiter / Network"
    location: Optional[str] = "India / Remote"
    experience_str: Optional[str] = "1 - 2 Years Exp"
    description: str
    post_url: str
    hr_email: Optional[str] = None
    apply_link: Optional[str] = None
    google_form_url: Optional[str] = None
    source: Optional[str] = "LinkedIn Post (#hiring)"
    posted_date_str: Optional[str] = "Today"

