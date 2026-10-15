from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class ResumeOut(BaseModel):
    id: int
    filename: str
    file_path: Optional[str] = None
    skills: Optional[str] = None
    experience_years: Optional[float] = 2.0
    summary: Optional[str] = None
    is_active: bool
    uploaded_at: datetime

    class Config:
        from_attributes = True

class ResumePathUploadRequest(BaseModel):
    file_path: str
