import json
import logging
import httpx
from typing import List
from fastapi import WebSocket
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.config import settings

logger = logging.getLogger(__name__)

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

async def send_external_alert(job_dict: dict):
    """
    Sends an instant notification alert to Telegram or Discord if configured.
    Non-blocking and safe: fails quietly if webhook isn't configured or fails.
    """
    title = job_dict.get("title", "Java Developer")
    company = job_dict.get("company", "Tech Company")
    score = job_dict.get("match_score", 90)
    exp = job_dict.get("experience_str", "2 Years Exp")
    location = job_dict.get("location", "India / Remote")
    apply_link = job_dict.get("apply_link", "")
    hr_email = job_dict.get("hr_email", "")

    # 1. Telegram Alert
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    if token and chat_id:
        try:
            tg_msg = (
                f"🎯 *New Job Alert ({score}% Fit)*\n\n"
                f"📌 *Role:* {title}\n"
                f"🏢 *Company:* {company}\n"
                f"📍 *Location:* {location}\n"
                f"⏳ *Experience:* {exp}\n"
            )
            if hr_email:
                tg_msg += f"📧 *HR Email:* `{hr_email}`\n"
            if apply_link:
                tg_msg += f"🔗 [Apply Here]({apply_link})\n"

            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": tg_msg,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": False
                    }
                )
        except Exception as e:
            logger.debug(f"Telegram alert error: {e}")

    # 2. Discord Webhook Alert
    discord_url = settings.DISCORD_WEBHOOK_URL
    if discord_url:
        try:
            embed = {
                "title": f"🎯 {title} @ {company}",
                "description": f"**Match Score:** {score}%\n**Experience:** {exp}\n**Location:** {location}",
                "color": 3447003,
                "fields": []
            }
            if hr_email:
                embed["fields"].append({"name": "HR Contact", "value": hr_email, "inline": True})
            if apply_link:
                embed["fields"].append({"name": "Application Link", "value": f"[Click Here to Apply]({apply_link})", "inline": False})

            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(discord_url, json={"embeds": [embed]})
        except Exception as e:
            logger.debug(f"Discord webhook error: {e}")

