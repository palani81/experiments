"""SMB filesystem abstraction — access NAS files over SMB without OS mounting.

Uses smbprotocol/smbclient for pure-Python SMB access.
Provides os-like functions: walk, stat, open_file, listdir, etc.
Supports multiple shares from the same or different hosts.
"""
from __future__ import annotations

import os
import tempfile
import shutil
import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional, BinaryIO

import smbclient
from smbprotocol.exceptions import SMBException, SMBAuthenticationError

logger = logging.getLogger("nas_explorer.smb_fs")

# Thread-safe temp file tracking for cleanup
_temp_files: set[str] = set()
_temp_lock = threading.Lock()

TEMP_DIR = None  # Set during init


@dataclass
class SMBSource:
    """A single SMB share or subfolder to index."""
    host: str
    share: str
    username: str
    password: str
    subfolder: str = "/"
    label: str = ""  # Display name, e.g. "Movies", "Documents"

    @property
    def smb_root(self) -> str:
        """Full SMB path to this source's root."""
        base = f"\\\\{self.host}\\{self.share}"
        if self.subfolder and self.subfolder != "/":
            sub = self.subfolder.replace("/", "\\").strip("\\")
            return f"{base}\\{sub}"
        return base

    @property
    def source_id(self) -> str:
        """Unique identifier for this source."""
        return f"{self.host}/{self.share}{self.subfolder}".rstrip("/")


@dataclass
class SMBFileInfo:
    """File information returned by stat operations."""
    name: str
    path: str  # SMB path
    relative_path: str  # Relative path for DB storage
    is_directory: bool
    size: int
    mtime: float  # Modification time as timestamp
    ctime: float  # Creation time as timestamp
    source_id: str  # Which source this belongs to


# ─── Session Management ──────────────────────────────────────────────────

_registered_sessions: set[str] = set()
_session_lock = threading.Lock()


def register_source(source: SMBSource):
    """Register SMB credentials for a source host."""
    with _session_lock:
        if source.host not in _registered_sessions:
            try:
                smbclient.register_session(
                    source.host,
                    username=source.username,
                    password=source.password,
                )
                _registered_sessions.add(source.host)
                logger.info(f"SMB session registered for {source.host}")
            except Exception as e:
                logger.error(f"Failed to register SMB session for {source.host}: {e}")
                raise


def init_temp_dir(cache_path: str):
    """Initialize temp directory for downloaded files."""
    global TEMP_DIR
    TEMP_DIR = os.path.join(cache_path, "_smb_temp")
    os.makedirs(TEMP_DIR, exist_ok=True)


# ─── Discovery & Testing ─────────────────────────────────────────────────

def discover_shares(host: str, username: str, password: str) -> list[str]:
    """Discover available SMB shares on a host."""
    try:
        # Register session temporarily
        smbclient.register_session(host, username=username, password=password)

        # List shares by trying to list root
        # smbclient doesn't have a direct share listing, so we use the lower-level API
        from smbprotocol.session import Session
        from smbprotocol.connection import Connection
        from smbprotocol.tree import TreeConnect

        # Alternative: use smbclient CLI if available, otherwise use protocol-level listing
        shares = _discover_shares_via_cli(host, username, password)
        if shares is not None:
            return shares

        # Fallback: try well-known share names
        common_shares = [
            "homes", "home", "music", "video", "photo", "public",
            "documents", "downloads", "media", "backup", "data",
            "share", "shared", "files", "nas",
        ]
        found = []
        for name in common_shares:
            try:
                smb_path = f"\\\\{host}\\{name}"
                smbclient.listdir(smb_path)
                found.append(name)
            except Exception:
                pass
        return found

    except SMBAuthenticationError:
        logger.warning(f"Auth failed discovering shares on {host}")
        return []
    except Exception as e:
        logger.warning(f"Share discovery failed for {host}: {e}")
        return []


def _discover_shares_via_cli(host: str, username: str, password: str) -> Optional[list[str]]:
    """Try using smbclient CLI for share discovery (more reliable)."""
    import subprocess
    try:
        cmd = ["smbclient", "-L", host, "-U", f"{username}%{password}"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        output = result.stdout + result.stderr

        shares = []
        in_shares = False
        for line in output.splitlines():
            line = line.strip()
            if "Sharename" in line and "Type" in line:
                in_shares = True
                continue
            if in_shares and line.startswith("---"):
                continue
            if in_shares and line:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "Disk":
                    share_name = parts[0]
                    if not share_name.endswith("$"):
                        shares.append(share_name)
            if in_shares and not line:
                break

        return shares if shares else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def test_connection(host: str, share: str, username: str, password: str) -> dict:
    """Test if we can connect to and list an SMB share."""
    try:
        smbclient.register_session(host, username=username, password=password)
        smb_path = f"\\\\{host}\\{share}"
        entries = smbclient.listdir(smb_path)
        # Filter out . and ..
        entries = [e for e in entries if e not in (".", "..")]
        return {
            "success": True,
            "message": f"Connected successfully. Found {len(entries)} items in share root.",
            "items_found": len(entries),
        }
    except SMBAuthenticationError:
        return {"success": False, "message": "Login failed — check username/password.", "items_found": 0}
    except SMBException as e:
        error_str = str(e)
        if "STATUS_BAD_NETWORK_NAME" in error_str:
            return {"success": False, "message": f"Share '{share}' not found on {host}.", "items_found": 0}
        return {"success": False, "message": f"SMB error: {error_str[:200]}", "items_found": 0}
    except OSError as e:
        if "timed out" in str(e).lower() or "unreachable" in str(e).lower():
            return {"success": False, "message": f"Cannot reach {host}. Check the IP/hostname.", "items_found": 0}
        return {"success": False, "message": f"Connection error: {str(e)[:200]}", "items_found": 0}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)[:200]}", "items_found": 0}


# ─── File Operations ──────────────────────────────────────────────────────

def walk(source: SMBSource) -> Iterator[tuple[str, list[str], list[str]]]:
    """
    Walk an SMB share like os.walk().
    Yields (smb_dirpath, dirnames, filenames).
    """
    try:
        for dirpath, dirnames, filenames in smbclient.walk(source.smb_root):
            yield dirpath, dirnames, filenames
    except Exception as e:
        logger.error(f"SMB walk failed for {source.smb_root}: {e}")
        return


def stat(smb_path: str) -> Optional[SMBFileInfo]:
    """Get file info for an SMB path."""
    try:
        st = smbclient.stat(smb_path)
        name = smb_path.replace("\\", "/").split("/")[-1]
        import stat as stat_module
        is_dir = stat_module.S_ISDIR(st.st_mode)
        return SMBFileInfo(
            name=name,
            path=smb_path,
            relative_path="",  # Caller sets this
            is_directory=is_dir,
            size=st.st_size,
            mtime=st.st_mtime,
            ctime=st.st_ctime if hasattr(st, 'st_ctime') else st.st_mtime,
            source_id="",
        )
    except Exception as e:
        logger.debug(f"SMB stat failed for {smb_path}: {e}")
        return None


def listdir(smb_path: str) -> list[str]:
    """List directory contents over SMB."""
    try:
        entries = smbclient.listdir(smb_path)
        return [e for e in entries if e not in (".", "..")]
    except Exception as e:
        logger.debug(f"SMB listdir failed for {smb_path}: {e}")
        return []


def open_file(smb_path: str, mode: str = "rb") -> BinaryIO:
    """Open a file over SMB. Returns a file-like object."""
    return smbclient.open_file(smb_path, mode=mode)


def read_bytes(smb_path: str, max_bytes: int = 0) -> bytes:
    """Read file contents over SMB."""
    with smbclient.open_file(smb_path, mode="rb") as f:
        if max_bytes > 0:
            return f.read(max_bytes)
        return f.read()


def exists(smb_path: str) -> bool:
    """Check if an SMB path exists."""
    try:
        smbclient.stat(smb_path)
        return True
    except Exception:
        return False


def is_dir(smb_path: str) -> bool:
    """Check if an SMB path is a directory."""
    try:
        import stat as stat_module
        st = smbclient.stat(smb_path)
        return stat_module.S_ISDIR(st.st_mode)
    except Exception:
        return False


# ─── Temp File Downloads ──────────────────────────────────────────────────
# For operations that need local files (ffmpeg, PIL, pdfplumber, etc.)

def download_to_temp(smb_path: str, suffix: str = "") -> str:
    """
    Download an SMB file to a local temp file.
    Returns the local temp file path.
    Caller should call cleanup_temp() when done.
    """
    if not TEMP_DIR:
        init_temp_dir("/tmp/nas_explorer_cache")

    if not suffix:
        # Preserve original extension
        name = smb_path.replace("\\", "/").split("/")[-1]
        if "." in name:
            suffix = "." + name.rsplit(".", 1)[1]

    fd, temp_path = tempfile.mkstemp(dir=TEMP_DIR, suffix=suffix)
    try:
        with smbclient.open_file(smb_path, mode="rb") as src:
            with os.fdopen(fd, "wb") as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)  # 1MB chunks

        with _temp_lock:
            _temp_files.add(temp_path)

        return temp_path
    except Exception:
        os.close(fd) if not os.get_inheritable(fd) else None
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def cleanup_temp(temp_path: str):
    """Remove a temp file created by download_to_temp."""
    try:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        with _temp_lock:
            _temp_files.discard(temp_path)
    except Exception as e:
        logger.debug(f"Temp cleanup failed for {temp_path}: {e}")


def cleanup_all_temps():
    """Remove all temp files."""
    with _temp_lock:
        for path in list(_temp_files):
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except Exception:
                pass
        _temp_files.clear()


# ─── Path Conversion ─────────────────────────────────────────────────────

def smb_to_relative(smb_path: str, source: SMBSource) -> str:
    """Convert an SMB path to a relative path for DB storage.

    Format: /<source_label_or_share>/relative/path
    This ensures uniqueness across multiple shares.
    """
    root = source.smb_root.rstrip("\\")
    # Normalize both paths for comparison
    norm_path = smb_path.replace("/", "\\").rstrip("\\")
    norm_root = root.replace("/", "\\")

    if norm_path == norm_root:
        label = source.label or source.share
        return f"/{label}"

    if norm_path.startswith(norm_root + "\\"):
        rel = norm_path[len(norm_root) + 1:].replace("\\", "/")
        label = source.label or source.share
        return f"/{label}/{rel}"

    # Fallback
    return "/" + smb_path.replace("\\", "/").split("/")[-1]


def relative_to_smb(relative_path: str, sources: list[SMBSource]) -> Optional[str]:
    """Convert a relative DB path back to an SMB path.

    Looks up which source the path belongs to based on the first component.
    """
    parts = relative_path.strip("/").split("/", 1)
    if not parts:
        return None

    source_label = parts[0]
    remaining = parts[1] if len(parts) > 1 else ""

    for source in sources:
        label = source.label or source.share
        if label == source_label:
            smb_path = source.smb_root
            if remaining:
                smb_path += "\\" + remaining.replace("/", "\\")
            return smb_path

    return None


def get_mime_type(smb_path: str, temp_path: str = None) -> str:
    """Detect MIME type for an SMB file."""
    # Try by extension first (fast, no download needed)
    import mimetypes
    name = smb_path.replace("\\", "/").split("/")[-1]
    mime, _ = mimetypes.guess_type(name)
    if mime:
        return mime

    # If we have a local temp copy, use python-magic
    if temp_path:
        try:
            import magic
            return magic.from_file(temp_path, mime=True)
        except Exception:
            pass

    return "application/octet-stream"
