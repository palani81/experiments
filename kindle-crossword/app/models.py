from typing import Literal, Optional

from pydantic import BaseModel, Field


class ProcessingOptions(BaseModel):
    auto_perspective: bool = True
    threshold_mode: Literal["adaptive", "otsu", "none"] = "adaptive"
    contrast_clip_limit: float = 3.0
    sharpness: float = 1.2


class JobResponse(BaseModel):
    id: int
    original_filename: str
    status: str
    created_at: str
    processed_at: Optional[str] = None
    sent_at: Optional[str] = None
    error_message: Optional[str] = None


class JobDetailResponse(JobResponse):
    processing_options: Optional[dict] = None


class SettingsRequest(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    kindle_email: Optional[str] = None


class SettingsResponse(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: str = ""
    smtp_use_tls: Optional[bool] = None
    kindle_email: Optional[str] = None

    @classmethod
    def from_settings(cls, settings: dict) -> "SettingsResponse":
        password = settings.get("smtp_password")
        port = settings.get("smtp_port")
        tls = settings.get("smtp_use_tls")
        return cls(
            smtp_host=settings.get("smtp_host"),
            smtp_port=int(port) if port is not None else None,
            smtp_user=settings.get("smtp_user"),
            smtp_password="****" if password else "",
            smtp_use_tls=str(tls).lower() in ("true", "1", "yes") if tls is not None else None,
            kindle_email=settings.get("kindle_email"),
        )


class UploadResponse(BaseModel):
    job_id: int
    status: str
    message: str
    preview_url: Optional[str] = None
