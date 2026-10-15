from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.settings import SearchConfig
from app.schemas.settings import SearchConfigOut, SearchConfigUpdate
from app.services.scheduler import scheduler, scheduled_job_search_task

router = APIRouter(prefix="/api/settings", tags=["Search Preferences"])

@router.get("", response_model=SearchConfigOut)
def get_settings(db: Session = Depends(get_db)):
    config = db.query(SearchConfig).first()
    if not config:
        config = SearchConfig(
            keywords="Java Developer, Spring Boot, Microservices",
            target_experience=2.0,
            experience_tolerance=0.5,
            location="India, Remote",
            auto_scrape_enabled=True,
            scrape_interval_minutes=30
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@router.post("", response_model=SearchConfigOut)
def update_settings(update_data: SearchConfigUpdate, db: Session = Depends(get_db)):
    config = db.query(SearchConfig).first()
    if not config:
        config = SearchConfig()
        db.add(config)
    
    for key, val in update_data.model_dump(exclude_unset=True).items():
        setattr(config, key, val)
        
    db.commit()
    db.refresh(config)

    # Dynamically update the scheduler interval if changed
    if config.auto_scrape_enabled and scheduler.running:
        try:
            scheduler.reschedule_job(
                "job_search_cron",
                trigger="interval",
                minutes=config.scrape_interval_minutes
            )
        except Exception:
            scheduler.add_job(
                scheduled_job_search_task,
                "interval",
                minutes=config.scrape_interval_minutes,
                id="job_search_cron",
                replace_existing=True
            )

    return config
