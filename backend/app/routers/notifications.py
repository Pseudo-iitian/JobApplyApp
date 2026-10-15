from typing import List
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.notification import Notification
from app.schemas.notification import NotificationOut
from app.services.notifier import manager

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("", response_model=List[NotificationOut])
def get_notifications(unread_only: bool = False, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(Notification)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()

@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif

@router.post("/mark-all-read")
def mark_all_notifications_read(db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.is_read == False).update({Notification.is_read: True})
    db.commit()
    return {"message": "All notifications marked as read."}

@router.delete("/clear")
def clear_all_notifications(db: Session = Depends(get_db)):
    db.query(Notification).delete()
    db.commit()
    return {"message": "All notifications cleared."}

@router.websocket("/ws")
async def websocket_notifications_endpoint(websocket: WebSocket):
    """Real-time WebSocket connection to stream live job discoveries and status alerts."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, listen for ping/pong or client messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
