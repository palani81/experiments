"""Security layer: path validation, auth, read-only enforcement."""
from __future__ import annotations

import logging
from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings

logger = logging.getLogger("nas_explorer.security")
security_scheme = HTTPBearer(auto_error=False)


# ─── Path Validation (SMB-based) ─────────────────────────────────────────

def get_smb_path(relative_path: str) -> str:
    """
    Convert a stored relative DB path to an SMB path.
    Returns the SMB path (\\\\host\\share\\path\\...).
    Raises HTTPException if path is invalid.
    """
    from .nas_manager import get_sources
    from .smb_fs import relative_to_smb, exists

    sources = get_sources()
    if not sources:
        raise HTTPException(status_code=503, detail="No NAS sources configured")

    smb_path = relative_to_smb(relative_path, sources)
    if not smb_path:
        raise HTTPException(status_code=404, detail="Path not found in any configured source")

    return smb_path


def get_relative_path(smb_path: str, source=None) -> str:
    """Convert an SMB path to a relative path for storage/display."""
    from .smb_fs import smb_to_relative
    if source:
        return smb_to_relative(smb_path, source)
    # If no source provided, try all sources
    from .nas_manager import get_sources
    for s in get_sources():
        rel = smb_to_relative(smb_path, s)
        if rel and rel != "/":
            return rel
    return "/"


# ─── Authentication ──────────────────────────────────────────────────────

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
    request: Request = None,
) -> bool:
    """Verify the bearer token matches the configured auth token."""
    # Allow unauthenticated access if token is the default (dev mode)
    if settings.auth_token == "change-me-to-a-secure-token":
        return True

    if credentials is None:
        # Check query param fallback (for preview URLs in img tags)
        if request and request.query_params.get("token") == settings.auth_token:
            return True
        raise HTTPException(status_code=401, detail="Missing authentication token")

    if credentials.credentials != settings.auth_token:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return True


# ─── Combined dependency ─────────────────────────────────────────────────

async def require_auth(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
    request: Request = None,
):
    """FastAPI dependency for protected endpoints."""
    return await verify_token(credentials, request)
