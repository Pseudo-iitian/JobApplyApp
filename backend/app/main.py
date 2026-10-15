import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models.settings import SearchConfig
from app.services.scheduler import start_scheduler, stop_scheduler
from app.services.scraper import run_job_search_cycle
from app.routers import jobs_router, resume_router, notifications_router, settings_router, auto_apply_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("JobApplyApp")

import asyncio
from app.models.job import Job

async def run_initial_discovery():
    try:
        await asyncio.sleep(2.0)  # Wait for server to finish binding and accept requests
        db = SessionLocal()
        try:
            job_count = db.query(Job).count()
            if job_count > 0:
                logger.info(f"Database already populated with {job_count} jobs. Skipping startup scrape.")
                return
            logger.info("Database empty; running initial background job discovery cycle (non-blocking)...")
            await run_job_search_cycle(db)
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Initial background discovery notice: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup:
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    # Seed default search config
    db = SessionLocal()
    try:
        config = db.query(SearchConfig).first()
        if not config:
            config = SearchConfig(
                keywords="Java Developer, Spring Boot, Microservices",
                target_experience=2.0,
                experience_tolerance=0.5,
                location="India, Remote",
                auto_scrape_enabled=True,
                scrape_interval_minutes=settings.SCRAPE_INTERVAL_MINUTES
            )
            db.add(config)
            db.commit()
    except Exception as e:
        logger.warning(f"Startup initial config notice: {e}")
    finally:
        db.close()

    # Launch non-blocking background discovery task
    asyncio.create_task(run_initial_discovery())

    # Launch 24/7 background scheduler
    start_scheduler()
    logger.info("Application startup completed successfully.")

    yield

    # Shutdown:
    logger.info("Shutting down background scheduler...")
    stop_scheduler()

app = FastAPI(
    title=settings.APP_NAME,
    description="24/7 Automated AI Job Application & Jira Kanban Tracking App",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for screenshots and artifacts
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

extension_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "extension")
if os.path.exists(extension_dir):
    app.mount("/extension", StaticFiles(directory=extension_dir), name="extension")

# Register API routers
app.include_router(jobs_router)
app.include_router(resume_router)
app.include_router(notifications_router)
app.include_router(settings_router)
app.include_router(auto_apply_router)

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "scheduler": "running 24/7",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
