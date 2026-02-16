"""Admin endpoints: scanning, health, system info."""

from fastapi import APIRouter, Depends

from ..database import query
from ..scanner import start_scan, get_scan_state, stop_scan
from ..security import require_auth
from ..models import ScanStatus

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/scan")
async def trigger_scan(
    full_scan: bool = False,
    _auth=Depends(require_auth),
):
    """Trigger a file scan (incremental by default, full if requested)."""
    result = start_scan(full_scan=full_scan)
    if "error" in result:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail=result["error"])
    return result


@router.get("/scan-status", response_model=ScanStatus)
async def scan_status(_auth=Depends(require_auth)):
    """Get current scan progress."""
    state = get_scan_state()

    total_est = state.get("total_estimate", 0)
    scanned = state.get("files_scanned", 0)
    progress = 0.0
    if total_est > 0:
        progress = min(100.0, (scanned / total_est) * 100)
    elif state["running"]:
        progress = -1  # Indeterminate

    return ScanStatus(
        scan_id=state.get("scan_id"),
        status="scanning" if state["running"] else "idle",
        files_scanned=scanned,
        files_added=state.get("files_added", 0),
        files_updated=state.get("files_updated", 0),
        files_removed=state.get("files_removed", 0),
        errors=state.get("errors", 0),
        current_source=state.get("current_source", ""),
        started_at=state.get("started_at"),
        progress_pct=progress,
    )


@router.post("/scan-stop")
async def trigger_scan_stop(_auth=Depends(require_auth)):
    """Stop a running scan."""
    return stop_scan()


@router.get("/scan-history")
async def scan_history(
    limit: int = 10,
    _auth=Depends(require_auth),
):
    """Get past scan results."""
    rows = query(
        "SELECT * FROM scan_log ORDER BY started_at DESC LIMIT ?",
        (limit,)
    )
    return [dict(r) for r in rows]


@router.get("/health")
async def health():
    """Health check — no auth required."""
    from ..nas_manager import get_connection_status
    conn_status = get_connection_status()
    db_ok = False
    try:
        result = query("SELECT COUNT(*) as cnt FROM files")
        db_ok = True
        file_count = result[0]["cnt"] if result else 0
    except Exception:
        file_count = 0

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "indexed_files": file_count,
        "nas_configured": conn_status.get("configured", False),
        "nas_connected": conn_status.get("connected", False),
        "sources_count": len(conn_status.get("sources", [])),
    }


@router.get("/tags")
async def list_all_tags(_auth=Depends(require_auth)):
    """List all unique tags with counts."""
    rows = query("""
        SELECT tag, COUNT(*) as count
        FROM file_tags
        GROUP BY tag
        ORDER BY count DESC
    """)
    return [dict(r) for r in rows]
