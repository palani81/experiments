"""Preview/thumbnail serving and file streaming endpoints."""

import os
import hashlib
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from ..database import query
from ..previews import get_preview_smb
from ..security import require_auth, get_smb_path
from ..smb_fs import download_to_temp, cleanup_temp, open_file, is_dir

router = APIRouter(prefix="/api", tags=["preview"])


@router.get("/preview/{file_id}")
async def serve_preview(
    file_id: int,
    size: str = Query("medium", description="Preview size: small, medium, large"),
    _auth=Depends(require_auth),
):
    """Serve a cached preview/thumbnail for a file."""
    rows = query("SELECT path, mime_type, file_hash FROM files WHERE id = ?", (file_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="File not found")

    row = rows[0]

    # Resolve to SMB path
    try:
        smb_path = get_smb_path(row["path"])
    except HTTPException:
        raise HTTPException(status_code=404, detail="File not accessible")

    # Generate or get cached preview
    preview_path = get_preview_smb(smb_path, row["mime_type"], row["file_hash"], size)

    if preview_path and os.path.exists(preview_path):
        return FileResponse(
            preview_path,
            media_type="image/webp",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    raise HTTPException(status_code=404, detail="No preview available")


@router.get("/stream/{file_id}")
async def stream_file(
    file_id: int,
    _auth=Depends(require_auth),
):
    """
    Stream a file from NAS over SMB (for in-browser video/audio playback, PDF viewing, etc.).
    Read-only — just sends the file bytes.
    """
    rows = query("SELECT path, mime_type, name, size FROM files WHERE id = ?", (file_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="File not found")

    row = rows[0]

    try:
        smb_path = get_smb_path(row["path"])
    except HTTPException:
        raise HTTPException(status_code=404, detail="File not accessible")

    mime_type = row["mime_type"] or "application/octet-stream"
    filename = row["name"]
    file_size = row["size"]

    # Stream the file in chunks from SMB
    def iter_smb_file():
        try:
            with open_file(smb_path) as f:
                while True:
                    chunk = f.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Stream error: {e}")

    headers = {
        "Content-Disposition": f'inline; filename="{filename}"',
        "Cache-Control": "public, max-age=3600",
    }
    if file_size:
        headers["Content-Length"] = str(file_size)

    return StreamingResponse(
        iter_smb_file(),
        media_type=mime_type,
        headers=headers,
    )
