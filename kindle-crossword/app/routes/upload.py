import json
import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import settings
from app.database import get_db
from app.image_processor import process_image
from app.models import ProcessingOptions, UploadResponse
from app.pdf_generator import generate_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "heic"}


def _sanitize_filename(filename: str) -> str:
    """Strip path separators and dangerous characters from filename."""
    name = filename.replace("/", "").replace("\\", "").replace("\x00", "")
    return name or "upload"


def _validate_extension(filename: str) -> str:
    """Validate file extension and return it lowercased."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '.{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )
    return ext


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile,
    auto_perspective: bool = Form(default=settings.auto_perspective),
    threshold_mode: str = Form(default=settings.threshold_mode),
    contrast_clip_limit: float = Form(default=settings.contrast_clip_limit),
    sharpness: float = Form(default=settings.sharpness),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    safe_name = _sanitize_filename(file.filename)
    _validate_extension(safe_name)

    options = ProcessingOptions(
        auto_perspective=auto_perspective,
        threshold_mode=threshold_mode,
        contrast_clip_limit=contrast_clip_limit,
        sharpness=sharpness,
    )

    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    upload_dir = Path(settings.upload_path).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = (upload_dir / unique_name).resolve()

    # Prevent path traversal
    if not str(saved_path).startswith(str(upload_dir)):
        raise HTTPException(status_code=400, detail="Invalid filename")

    content = await file.read()
    saved_path.write_bytes(content)

    now = datetime.utcnow().isoformat()
    options_json = options.model_dump_json()

    with get_db() as db:
        cursor = db.execute(
            """INSERT INTO jobs (original_filename, original_path, status, processing_options, created_at)
               VALUES (?, ?, 'processing', ?, ?)""",
            (safe_name, str(saved_path), options_json, now),
        )
        job_id = cursor.lastrowid

    try:
        output_dir = Path(settings.output_path).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        processed_path = str((output_dir / f"{job_id}_processed.png").resolve())
        pdf_path = str((output_dir / f"{job_id}_output.pdf").resolve())

        process_image(str(saved_path), processed_path, options.model_dump())
        generate_pdf([processed_path], pdf_path)

        processed_at = datetime.utcnow().isoformat()
        with get_db() as db:
            db.execute(
                """UPDATE jobs SET status='processed', processed_path=?, pdf_path=?, processed_at=?
                   WHERE id=?""",
                (processed_path, pdf_path, processed_at, job_id),
            )

        return UploadResponse(
            job_id=job_id,
            status="processed",
            message="Image processed successfully",
            preview_url=f"/api/jobs/{job_id}/preview",
        )

    except Exception as e:
        logger.exception("Processing failed for job %s", job_id)
        with get_db() as db:
            db.execute(
                "UPDATE jobs SET status='failed', error_message=? WHERE id=?",
                (str(e), job_id),
            )
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")


@router.post("/jobs/{job_id}/send")
async def send_to_kindle(job_id: int):
    with get_db() as db:
        row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    if row["status"] != "processed":
        raise HTTPException(
            status_code=400,
            detail=f"Job is not ready to send (status: {row['status']})",
        )

    try:
        from app import email_sender
    except ImportError:
        raise HTTPException(
            status_code=500, detail="Email sender module is not available"
        )

    try:
        email_sender.send_to_kindle(row["pdf_path"])
    except Exception as e:
        logger.exception("Failed to send job %s to Kindle", job_id)
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")

    sent_at = datetime.utcnow().isoformat()
    with get_db() as db:
        db.execute(
            "UPDATE jobs SET status='sent', sent_at=? WHERE id=?",
            (sent_at, job_id),
        )

    return {"status": "sent", "message": "PDF sent to Kindle successfully"}


@router.get("/jobs/{job_id}/preview")
async def get_preview(job_id: int):
    with get_db() as db:
        row = db.execute(
            "SELECT processed_path FROM jobs WHERE id=?", (job_id,)
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    if not row["processed_path"]:
        raise HTTPException(status_code=404, detail="No processed image available")

    file_path = Path(row["processed_path"]).resolve()
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Processed image file not found")

    return FileResponse(str(file_path), media_type="image/png")


@router.get("/jobs/{job_id}/pdf")
async def get_pdf(job_id: int):
    with get_db() as db:
        row = db.execute(
            "SELECT pdf_path, original_filename FROM jobs WHERE id=?", (job_id,)
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    if not row["pdf_path"]:
        raise HTTPException(status_code=404, detail="No PDF available")

    file_path = Path(row["pdf_path"]).resolve()
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="PDF file not found")

    download_name = Path(row["original_filename"]).stem + ".pdf"

    return FileResponse(
        str(file_path),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )
