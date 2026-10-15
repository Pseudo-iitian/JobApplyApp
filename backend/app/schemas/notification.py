from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    job_id: Optional[int] = None
    notification_type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
