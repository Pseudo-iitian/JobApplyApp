import os
import re
from typing import Dict, Any, List
from pypdf import PdfReader

from datetime import datetime

COMMON_JAVA_SKILLS = [
    "Java", "Core Java", "Java 8", "Java 11", "Java 17", "Spring", "Spring Boot",
    "Spring MVC", "Spring Security", "Hibernate", "JPA", "Microservices",
    "REST API", "RESTful Web Services", "SQL", "MySQL", "PostgreSQL", "Oracle",
    "MongoDB", "Docker", "Kubernetes", "AWS", "Kafka", "RabbitMQ", "Redis",
    "JUnit", "Mockito", "Maven", "Gradle", "Git", "GitHub", "GitLab",
    "CI/CD", "Jenkins", "Design Patterns", "Multithreading", "Data Structures"
]

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts raw text content from a PDF file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at: {file_path}")
    
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()

def extract_skills_heuristic(text: str) -> List[str]:
    """Scans resume text for common Java/Backend engineering skills."""
    found_skills = set()
    text_lower = text.lower()
    
    for skill in COMMON_JAVA_SKILLS:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            found_skills.add(skill)
            
    return sorted(list(found_skills))

def estimate_experience_years(text: str) -> float:
    """Heuristic extraction of experience in years from resume text."""
    # Matches patterns like "2 years of experience", "2+ yrs", "2.5 years"
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience", text, re.IGNORECASE)
    if matches:
        try:
            val = float(matches[0])
            if 0.5 <= val <= 30:
                return val
        except ValueError:
            pass
    
    # Check for simple "experience: 2 years"
    matches2 = re.findall(r"experience\s*[:\-]\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", text, re.IGNORECASE)
    if matches2:
        try:
            val = float(matches2[0])
            if 0.5 <= val <= 30:
                return val
        except ValueError:
            pass

    # Check year ranges like "2022 - Present", "2022 - 2024"
    current_year = datetime.now().year
    year_ranges = re.findall(r"(20\d\d)\s*(?:-|to)\s*(present|current|20\d\d)", text, re.IGNORECASE)
    total_years = 0.0
    for start_yr, end_yr in year_ranges:
        try:
            s = int(start_yr)
            e = current_year if end_yr.lower() in ("present", "current") else int(end_yr)
            diff = float(e - s)
            if 0 < diff <= 20:
                total_years = max(total_years, diff)
        except Exception:
            continue
    if total_years > 0:
        return total_years

    return 2.0  # Default sensible estimate for candidate

