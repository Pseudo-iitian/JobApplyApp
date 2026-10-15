import logging
from datetime import datetime
from typing import Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app.config import settings

logger = logging.getLogger("JobHunter-24/7")

scheduler = AsyncIOScheduler()

SCHEDULER_STATS: Dict[str, Any] = {
    "is_running": False,
    "total_runs": 0,
    "last_run_at": None,
    "last_jobs_found": 0,
    "status": "idle",
    "interval_minutes": 5
}

def get_scheduler_status() -> Dict[str, Any]:
    SCHEDULER_STATS["is_running"] = scheduler.running
    return dict(SCHEDULER_STATS)

async def scheduled_job_search_task():
    """Background task running continuously 24/7 to fetch and notify new jobs."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"⏰ [24/7 Heartbeat] Scheduled hunt cycle #{SCHEDULER_STATS['total_runs'] + 1} started at {now_str}")
    
    SCHEDULER_STATS["status"] = "hunting"
    SCHEDULER_STATS["last_run_at"] = now_str
    
    from app.services.scraper import run_job_search_cycle, record_log
    record_log("INFO", f"⏰ [24/7 Scheduler Heartbeat] Auto-hunt cycle #{SCHEDULER_STATS['total_runs'] + 1} initiated.")
    
    db = SessionLocal()
    try:
        result = await run_job_search_cycle(db)
        count = result.get('new_jobs_count', 0)
        SCHEDULER_STATS["total_runs"] += 1
        SCHEDULER_STATS["last_jobs_found"] = count
        SCHEDULER_STATS["status"] = "idle"
        record_log("INFO", f"✔ [24/7 Scheduler Heartbeat] Cycle completed. Discovered {count} new 2-year Java jobs.")
    except Exception as e:
        SCHEDULER_STATS["status"] = "error"
        logger.error(f"❌ [24/7 Scheduler Heartbeat] Error during scheduled search: {e}", exc_info=True)
        record_log("ERROR", f"❌ Scheduler error: {str(e)}")
    finally:
        db.close()

def start_scheduler():
    """Starts the 24/7 background scheduler."""
    if not scheduler.running:
        interval = getattr(settings, "SCRAPE_INTERVAL_MINUTES", 5) or 5
        SCHEDULER_STATS["interval_minutes"] = interval
        scheduler.add_job(
            scheduled_job_search_task,
            "interval",
            minutes=interval,
            id="job_search_cron",
            replace_existing=True
        )
        scheduler.start()
        SCHEDULER_STATS["is_running"] = True
        logger.info(f"🚀 [24/7 Scheduler Active] Multi-agent continuous hunter running every {interval} minutes.")

def stop_scheduler():
    """Shuts down the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown()
        SCHEDULER_STATS["is_running"] = False
        logger.info("🛑 [24/7 Scheduler] Background hunter stopped gracefully.")
