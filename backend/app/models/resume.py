from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime
from app.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(1000), nullable=True)
    raw_text = Column(Text, nullable=False)
    skills = Column(Text, nullable=True)  # JSON formatted string of skills
    experience_years = Column(Float, default=2.0)
    summary = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, index=True)
