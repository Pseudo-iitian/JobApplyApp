import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv

# Reliably load .env from backend directory or project root
_backend_dir = Path(__file__).resolve().parent.parent
_root_dir = _backend_dir.parent
if (_backend_dir / ".env").exists():
    load_dotenv(_backend_dir / ".env")
elif (_root_dir / ".env").exists():
    load_dotenv(_root_dir / ".env")
else:
    load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "JobApplyApp - AI Automated Job Hunter"
    DEBUG: bool = True
    
    # Database: Supports SQLite by default or AWS PostgreSQL if provided
    # Example PostgreSQL: postgresql://username:password@aws-rds-host:5432/database_name
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./jobapply.db")
    
    # LLM Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Scraping & Scheduler Settings
    SCRAPE_INTERVAL_MINUTES: int = 5
    DEFAULT_KEYWORDS: str = "Java Developer, Spring Boot, Microservices"
    DEFAULT_EXPERIENCE: float = 2.0
    DEFAULT_LOCATION: str = "India, Remote"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]
    
    class Config:
        env_file = str(_backend_dir / ".env")
        extra = "allow"

settings = Settings()
