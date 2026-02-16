"""Setup wizard API endpoints — NAS connection, testing, multi-share management."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..smb_fs import discover_shares, test_connection
from ..nas_manager import (
    get_connection_status,
    add_source,
    remove_source,
    get_sources,
)
from ..scanner import start_scan, stop_scan, get_scan_state

router = APIRouter(prefix="/api/setup", tags=["setup"])


class NASConnectRequest(BaseModel):
    host: str
    share: str
    username: str
    password: str
    subfolder: str = "/"
    label: str = ""  # Optional display name


class NASTestRequest(BaseModel):
    host: str
    username: str = ""
    password: str = ""


class NASRemoveRequest(BaseModel):
    source_id: str


# ─── No auth on setup endpoints (needed before first config) ──────────


@router.get("/status")
async def setup_status():
    """
    Get current NAS connection status.
    Frontend uses this to decide: show setup wizard or main app.
    """
    return get_connection_status()


@router.post("/discover")
async def discover_nas_shares(req: NASTestRequest):
    """Discover available SMB shares on a host."""
    if not req.host:
        raise HTTPException(status_code=400, detail="Host is required")

    shares = discover_shares(req.host, req.username, req.password)
    return {
        "host": req.host,
        "shares": shares,
        "message": f"Found {len(shares)} shares" if shares else "No shares found (check credentials or try entering the share name manually)",
    }


@router.post("/test")
async def test_nas_connection(req: NASConnectRequest):
    """Test NAS connection without saving."""
    if not req.host or not req.share:
        raise HTTPException(status_code=400, detail="Host and share are required")

    result = test_connection(req.host, req.share, req.username, req.password)
    return result


@router.post("/add-source")
async def add_nas_source(req: NASConnectRequest):
    """
    Add a new NAS source (share/folder). Supports multiple sources.
    Tests connection first, then saves and optionally starts scan.
    """
    if not req.host or not req.share:
        raise HTTPException(status_code=400, detail="Host and share are required")

    # Step 1: Test connection
    test_result = test_connection(req.host, req.share, req.username, req.password)
    if not test_result["success"]:
        return {
            "success": False,
            "step": "test",
            "message": test_result["message"],
        }

    # Step 2: Add source to config
    result = add_source(
        host=req.host,
        share=req.share,
        username=req.username,
        password=req.password,
        subfolder=req.subfolder,
        label=req.label or req.share,
    )

    if not result["success"]:
        return result

    # Step 3: Auto-trigger scan
    scan_result = start_scan(full_scan=True)

    return {
        "success": True,
        "step": "complete",
        "message": f"Source '{req.label or req.share}' added and scanning started!",
        "source_id": result.get("source_id"),
        "scan_started": "error" not in scan_result,
    }


# Keep /connect as alias for backward compatibility
@router.post("/connect")
async def connect_to_nas(req: NASConnectRequest):
    """Connect to NAS (alias for add-source)."""
    return await add_nas_source(req)


@router.post("/remove-source")
async def remove_nas_source(req: NASRemoveRequest):
    """
    Remove a NAS source.
    If a scan is running, stop it first, then remove the source and purge its
    indexed data from the DB, then restart the scan for remaining sources.
    """
    import time

    # Step 1: Stop any running scan
    scan_was_running = get_scan_state()["running"]
    if scan_was_running:
        stop_scan()
        # Wait briefly for scan thread to notice the cancel flag
        for _ in range(20):  # up to 2 seconds
            if not get_scan_state()["running"]:
                break
            time.sleep(0.1)

    # Step 2: Remove source from config + purge DB entries
    result = remove_source(req.source_id)

    if not result["success"]:
        return result

    # Step 3: Restart scan for remaining sources (if scan was running or sources remain)
    remaining = get_sources()
    scan_restarted = False
    if remaining and scan_was_running:
        scan_result = start_scan(full_scan=False)
        scan_restarted = "error" not in scan_result

    result["scan_restarted"] = scan_restarted
    return result


@router.get("/sources")
async def list_sources():
    """List all configured NAS sources."""
    sources = get_sources()
    return {
        "sources": [
            {
                "host": s.host,
                "share": s.share,
                "label": s.label,
                "subfolder": s.subfolder,
                "source_id": s.source_id,
            }
            for s in sources
        ]
    }


@router.get("/discover-available")
async def discover_available():
    """
    Discover all shares on the NAS using saved credentials.
    Returns all shares with a flag indicating which are already added.
    Used by the in-app 'Add Source' dialog so user doesn't re-enter credentials.
    """
    sources = get_sources()
    if not sources:
        return {"success": False, "message": "No NAS configured yet.", "shares": []}

    # Use credentials from the first source
    first = sources[0]
    added_shares = {s.share for s in sources}

    all_shares = discover_shares(first.host, first.username, first.password)

    return {
        "success": True,
        "host": first.host,
        "shares": [
            {"name": s, "added": s in added_shares}
            for s in all_shares
        ],
        "message": f"Found {len(all_shares)} shares on {first.host}",
    }


@router.post("/quick-add")
async def quick_add_source(req: NASRemoveRequest):
    """
    Quickly add a share by name, using saved credentials from existing sources.
    The source_id field is used as the share name here.
    """
    sources = get_sources()
    if not sources:
        raise HTTPException(status_code=400, detail="No NAS configured yet")

    first = sources[0]
    share_name = req.source_id  # Reusing source_id field as share name

    # Test and add using saved credentials
    test_result = test_connection(first.host, share_name, first.username, first.password)
    if not test_result["success"]:
        return {"success": False, "message": test_result["message"]}

    result = add_source(
        host=first.host,
        share=share_name,
        username=first.username,
        password=first.password,
        label=share_name,
    )

    if not result["success"]:
        return result

    # Trigger scan for new content
    scan_result = start_scan(full_scan=True)

    return {
        "success": True,
        "message": f"'{share_name}' added and scanning started!",
        "scan_started": "error" not in scan_result,
    }


@router.post("/scan")
async def trigger_scan(full: bool = False):
    """Trigger a scan of all configured sources."""
    result = start_scan(full_scan=full)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
