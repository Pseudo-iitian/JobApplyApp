from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.auto_apply import AutoApplyProfile, PortalCredential, AutoApplyLog
from app.services.auto_apply_agent import run_auto_apply_cycle

router = APIRouter(prefix="/api/auto-apply", tags=["Auto-Apply Agent"])

class AutoApplyProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    current_company: Optional[str] = None
    current_designation: Optional[str] = None
    total_experience: Optional[str] = None
    current_ctc: Optional[str] = None
    expected_ctc: Optional[str] = None
    notice_period: Optional[str] = None
    available_in_30_days: Optional[bool] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    resume_path: Optional[str] = None
    default_portal_password: Optional[str] = None
    cover_letter_template: Optional[str] = None
    max_exp_allowed: Optional[float] = None
    batch_size: Optional[int] = None

class AutoApplyRunRequest(BaseModel):
    batch_size: int = 5
    auto_open_browser: bool = True

@router.get("/profile")
def get_auto_apply_profile(db: Session = Depends(get_db)):
    profile = db.query(AutoApplyProfile).first()
    if not profile:
        profile = AutoApplyProfile()
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@router.put("/profile")
def update_auto_apply_profile(update_data: AutoApplyProfileUpdate, db: Session = Depends(get_db)):
    profile = db.query(AutoApplyProfile).first()
    if not profile:
        profile = AutoApplyProfile()
        db.add(profile)

    for field, val in update_data.model_dump(exclude_unset=True).items():
        if val is not None:
            setattr(profile, field, val)

    db.commit()
    db.refresh(profile)
    return profile

@router.get("/credentials")
def get_saved_portal_credentials(db: Session = Depends(get_db)):
    return db.query(PortalCredential).order_by(PortalCredential.id.desc()).all()

@router.get("/logs")
def get_auto_apply_logs(db: Session = Depends(get_db)):
    return db.query(AutoApplyLog).order_by(AutoApplyLog.id.desc()).limit(50).all()

@router.post("/run")
async def trigger_auto_apply_agent(req: AutoApplyRunRequest, db: Session = Depends(get_db)):
    """Runs the Auto-Apply Agent on the top batch_size jobs from DISCOVERED."""
    result = await run_auto_apply_cycle(
        db, 
        batch_size=req.batch_size,
        auto_open_browser=req.auto_open_browser
    )
    return result

@router.post("/stop")
async def stop_auto_apply_agent():
    """Stops any currently running Auto-Apply Agent cycle immediately."""
    from app.services.auto_apply_agent import request_stop_agent
    from app.services.notifier import manager
    request_stop_agent()
    await manager.broadcast({
        "event": "AUTO_APPLY_STOPPED",
        "message": "Autonomous Agent execution stopped by user."
    })
    return {"status": "stopped", "message": "Stop signal sent to Auto-Apply Agent."}

@router.get("/status")
def get_auto_apply_agent_status():
    """Returns current active status of the Auto-Apply Agent."""
    from app.services.auto_apply_agent import is_agent_active
    return {"is_running": is_agent_active()}
