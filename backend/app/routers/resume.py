import os
import shutil
import json
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.resume import Resume
from app.schemas.resume import ResumeOut, ResumePathUploadRequest
from app.services.resume_parser import extract_text_from_pdf, extract_skills_heuristic, estimate_experience_years

router = APIRouter(prefix="/api/resume", tags=["Resume Management"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=ResumeOut)
async def upload_resume_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Uploads a PDF resume, parses its text, skills, and experience."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported currently.")

    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        raw_text = extract_text_from_pdf(save_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read PDF: {str(e)}")

    skills = extract_skills_heuristic(raw_text)
    exp = estimate_experience_years(raw_text)

    # Deactivate previous resumes
    db.query(Resume).update({Resume.is_active: False})

    new_resume = Resume(
        filename=file.filename,
        file_path=save_path,
        raw_text=raw_text,
        skills=json.dumps(skills),
        experience_years=exp,
        summary=f"Parsed Java Developer profile with {exp} years experience.",
        is_active=True
    )
    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)
    return new_resume

@router.post("/file-path", response_model=ResumeOut)
def upload_resume_by_path(req: ResumePathUploadRequest, db: Session = Depends(get_db)):
    """Accepts a local file path (e.g. /home/user/resume.pdf) to parse."""
    path = os.path.expanduser(req.file_path.strip())
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File not found at path: {path}")

    if not path.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="The file specified must be a PDF document.")

    try:
        raw_text = extract_text_from_pdf(path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF at path: {str(e)}")

    skills = extract_skills_heuristic(raw_text)
    exp = estimate_experience_years(raw_text)

    db.query(Resume).update({Resume.is_active: False})

    new_resume = Resume(
        filename=os.path.basename(path),
        file_path=path,
        raw_text=raw_text,
        skills=json.dumps(skills),
        experience_years=exp,
        summary=f"Parsed Java Developer profile from path with {exp} years experience.",
        is_active=True
    )
    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)
    return new_resume

@router.get("/active", response_model=ResumeOut)
def get_active_resume(db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.is_active == True).order_by(Resume.uploaded_at.desc()).first()
    if not resume:
        raise HTTPException(status_code=404, detail="No active resume uploaded yet.")
    return resume
