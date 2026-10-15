from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class SearchConfigBase(BaseModel):
    full_name: str = "Abhishek Verma"
    email: str = "abhishek.verma.6561@gmail.com"
    phone: str = "+91-6307801566"
    resume_path: str = "/home/abhishek_verma/Desktop/Abhishek_Verma_Resume.pdf"
    current_ctc: str = "6 LPA"
    expected_ctc: str = "12 - 15 LPA"
    keywords: str = "Spring Boot, Java Developer, Microservices, Backend Developer"
    target_experience: float = 2.0
    experience_tolerance: float = 0.5
    location: str = "All India, Remote, Noida, Bangalore, Pune, Hyderabad, Gurgaon"
    auto_scrape_enabled: bool = True
    scrape_interval_minutes: int = 30

class SearchConfigUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    resume_path: Optional[str] = None
    current_ctc: Optional[str] = None
    expected_ctc: Optional[str] = None
    keywords: Optional[str] = None
    target_experience: Optional[float] = None
    experience_tolerance: Optional[float] = None
    location: Optional[str] = None
    auto_scrape_enabled: Optional[bool] = None
    scrape_interval_minutes: Optional[int] = None

class SearchConfigOut(SearchConfigBase):
    id: int
    last_scraped_at: Optional[datetime] = None

    class Config:
        from_attributes = True
