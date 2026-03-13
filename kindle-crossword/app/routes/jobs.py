import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.database import get_db
from app.models import JobDetailResponse, JobResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    with get_db() as db:
        rows = db.execute(
            """SELECT id, original_filename, status, created_at, processed_at, sent_at, error_message
               FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (limit, offset),
        ).fetchall()

    return [JobResponse(**dict(row)) for row in rows]


@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: int):
    with get_db() as db:
        row = db.execute(
            """SELECT id, original_filename, status, created_at, processed_at, sent_at,
                      error_message, processing_options
               FROM jobs WHERE id=?""",
            (job_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    data = dict(row)
    options_raw = data.pop("processing_options", None)
    if options_raw:
        try:
            data["processing_options"] = json.loads(options_raw)
        except (json.JSONDecodeError, TypeError):
            data["processing_options"] = None
    else:
        data["processing_options"] = None

    return JobDetailResponse(**data)


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: int):
    with get_db() as db:
        row = db.execute(
            "SELECT original_path, processed_path, pdf_path FROM jobs WHERE id=?",
            (job_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Job not found")

    # Delete associated files
    for path_field in ("original_path", "processed_path", "pdf_path"):
        file_path = row[path_field]
        if file_path:
            p = Path(file_path)
            if p.is_file():
                try:
                    p.unlink()
                except OSError:
                    logger.warning("Failed to delete file: %s", file_path)

    with get_db() as db:
        db.execute("DELETE FROM jobs WHERE id=?", (job_id,))

    return {"status": "deleted"}
