import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

from fastapi import APIRouter, HTTPException

from app.crypto import decrypt, encrypt
from app.database import get_db
from app.models import SettingsRequest, SettingsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

SETTINGS_KEYS = {
    "smtp_host",
    "smtp_port",
    "smtp_user",
    "smtp_password",
    "smtp_use_tls",
    "kindle_email",
}


def _load_settings() -> dict:
    """Load all settings from the app_settings table."""
    with get_db() as db:
        rows = db.execute("SELECT key, value FROM app_settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    raw = _load_settings()
    return SettingsResponse.from_settings(raw)


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(request: SettingsRequest):
    now = datetime.utcnow().isoformat()
    updates = {
        k: v
        for k, v in request.model_dump().items()
        if v is not None and k in SETTINGS_KEYS
    }

    if not updates:
        raise HTTPException(status_code=400, detail="No settings provided to update")

    with get_db() as db:
        for key, value in updates.items():
            store_value = encrypt(str(value)) if key == "smtp_password" else str(value)
            db.execute(
                """INSERT INTO app_settings (key, value, updated_at)
                   VALUES (?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at""",
                (key, store_value, now),
            )

    raw = _load_settings()
    return SettingsResponse.from_settings(raw)


@router.post("/settings/test-email")
async def test_email():
    raw = _load_settings()

    smtp_host = raw.get("smtp_host")
    smtp_port = raw.get("smtp_port")
    smtp_user = raw.get("smtp_user")
    smtp_password = decrypt(raw.get("smtp_password", ""))
    smtp_use_tls = raw.get("smtp_use_tls")
    kindle_email = raw.get("kindle_email")

    if not all([smtp_host, smtp_port, smtp_user, smtp_password, kindle_email]):
        raise HTTPException(
            status_code=400,
            detail="Incomplete email settings. Please configure SMTP host, port, user, password, and Kindle email.",
        )

    try:
        port = int(smtp_port)
        use_tls = str(smtp_use_tls).lower() in ("true", "1", "yes")

        msg = MIMEText("This is a test email from Kindle Crossword app.")
        msg["Subject"] = "Kindle Crossword - Test Email"
        msg["From"] = smtp_user
        msg["To"] = kindle_email

        if use_tls:
            server = smtplib.SMTP(smtp_host, port)
            server.starttls()
        else:
            server = smtplib.SMTP(smtp_host, port)

        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, kindle_email, msg.as_string())
        server.quit()

        return {"status": "success", "message": f"Test email sent to {kindle_email}"}

    except Exception as e:
        logger.exception("Test email failed")
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {e}")
