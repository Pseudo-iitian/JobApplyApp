import json
from typing import List
from fastapi import WebSocket
from sqlalchemy.orm import Session
from app.models.notification import Notification

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        payload = json.dumps(message)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

def create_notification(db: Session, title: str, message: str, job_id: int = None, notification_type: str = "NEW_JOB") -> Notification:
    """Creates a notification record in the database."""
    notification = Notification(
        title=title,
        message=message,
        job_id=job_id,
        notification_type=notification_type,
        is_read=False
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
