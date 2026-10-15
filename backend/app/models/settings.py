from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from app.database import Base

class SearchConfig(Base):
    __tablename__ = "search_configs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Candidate Profile Info
    full_name = Column(String(255), default="Abhishek Verma")
    email = Column(String(255), default="abhishek.verma.6561@gmail.com")
    phone = Column(String(100), default="+91-6307801566")
    resume_path = Column(String(1000), default="/home/abhishek_verma/Desktop/Abhishek_Verma_Resume.pdf")
    current_ctc = Column(String(100), default="6 LPA")
    expected_ctc = Column(String(100), default="12 - 15 LPA")

    # Search & Filter preferences
    keywords = Column(String(500), default="Spring Boot, Java Developer, Microservices, Backend Developer")
    target_experience = Column(Float, default=2.0)
    experience_tolerance = Column(Float, default=0.5)
    location = Column(String(500), default="All India, Remote, Noida, Bangalore, Pune, Hyderabad, Gurgaon")
    
    # 24/7 Background Scheduler settings
    auto_scrape_enabled = Column(Boolean, default=True)
    scrape_interval_minutes = Column(Integer, default=30)
    last_scraped_at = Column(DateTime, nullable=True)
