from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Index
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), default="Remote / Flexible")
    experience_required = Column(Float, default=2.0, index=True)
    experience_str = Column(String(100), default="2 Years")
    description = Column(Text, nullable=True)
    
    # Contact & Application Links
    apply_link = Column(String(1000), nullable=True)
    post_url = Column(String(1000), nullable=True)
    hr_email = Column(String(255), nullable=True, index=True)
    google_form_url = Column(String(1000), nullable=True)
    
    # Source tracking
    source = Column(String(100), default="Online Scraper")
    source_id = Column(String(255), unique=True, index=True, nullable=True)
    
    # Jira-like ATS Stage
    # DISCOVERED, APPLIED, SCREENING, INTERVIEWING, OFFER, REJECTED
    status = Column(String(50), default="DISCOVERED", index=True)
    
    # AI Matching & Tailoring
    match_score = Column(Integer, default=85)
    match_reasons = Column(Text, nullable=True)
    tailored_resume = Column(Text, nullable=True)
    tailored_cover_letter = Column(Text, nullable=True)
    hr_email_draft = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    posted_at = Column(DateTime, default=datetime.utcnow, nullable=True, index=True)
    posted_date_str = Column(String(100), default="Recently", nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    # Composite and performance indexes for ultra-low latency queries
    __table_args__ = (
        Index("ix_jobs_status_updated", "status", "updated_at"),
        Index("ix_jobs_exp_status", "experience_required", "status"),
        Index("ix_jobs_posted_at", "posted_at"),
        Index("ix_jobs_posted_created", "posted_at", "created_at", "id"),
        Index("ix_jobs_status_posted", "status", "posted_at"),
        Index("ix_jobs_status_created", "status", "created_at"),
        Index("ix_jobs_apply_link", "apply_link"),
        Index("ix_jobs_post_url", "post_url"),
        Index("ix_jobs_company_title", "company", "title"),
    )
