from app.routers.jobs import router as jobs_router
from app.routers.resume import router as resume_router
from app.routers.notifications import router as notifications_router
from app.routers.settings import router as settings_router
from app.routers.auto_apply import router as auto_apply_router

__all__ = ["jobs_router", "resume_router", "notifications_router", "settings_router", "auto_apply_router"]
