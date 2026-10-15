from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from app.database import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(String(1000), nullable=False)
    job_id = Column(Integer, nullable=True, index=True)
    notification_type = Column(String(50), default="NEW_JOB")
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_notifications_read_created", "is_read", "created_at"),
    )
