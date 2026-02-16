"""NAS connection manager — handles multi-share connections via pure SMB.

No OS-level mounting required. Uses smbprotocol for direct SMB access.
Supports multiple shares/folders from one or more NAS devices.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional

from .config import settings
from .smb_fs import SMBSource, register_source, test_connection, discover_shares
from .database import get_connection
from .crypto import encrypt, decrypt, is_encrypted

logger = logging.getLogger("nas_explorer.nas_manager")

CONFIG_FILE = None  # Set during init


def _config_path() -> str:
    """Get path to saved NAS config."""
    global CONFIG_FILE
    if CONFIG_FILE is None:
        data_dir = Path(settings.database_path).parent
        data_dir.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE = str(data_dir / "nas_connection.json")
    return CONFIG_FILE


# ─── Config Persistence ──────────────────────────────────────────────────

def save_config(config: dict):
    """Save NAS configuration to disk with encrypted credentials."""
    path = _config_path()

    # Deep-copy and encrypt sensitive fields before writing
    safe_config = {"sources": []}
    for src in config.get("sources", []):
        entry = dict(src)
        if entry.get("password") and not is_encrypted(entry["password"]):
            entry["password"] = encrypt(entry["password"])
        if entry.get("username") and not is_encrypted(entry["username"]):
            entry["username"] = encrypt(entry["username"])
        safe_config["sources"].append(entry)

    with open(path, "w") as f:
        json.dump(safe_config, f, indent=2)
    logger.info(f"NAS config saved with {len(safe_config['sources'])} sources (credentials encrypted)")


def load_config() -> Optional[dict]:
    """Load saved NAS configuration from disk, decrypting credentials."""
    path = _config_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            config = json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load NAS config: {e}")
        return None

    # Decrypt credentials and auto-migrate any plaintext entries
    needs_resave = False
    for src in config.get("sources", []):
        if src.get("password"):
            if not is_encrypted(src["password"]):
                needs_resave = True  # Found plaintext — will re-save encrypted
            src["password"] = decrypt(src["password"])
        if src.get("username"):
            if not is_encrypted(src["username"]):
                needs_resave = True
            src["username"] = decrypt(src["username"])

    # Auto-migrate: re-save with encryption if any plaintext was found
    if needs_resave:
        logger.info("Migrating plaintext credentials to encrypted storage")
        save_config(config)

    return config


def get_sources() -> list[SMBSource]:
    """Load all configured SMB sources."""
    config = load_config()
    if not config:
        return []

    sources = []
    for src in config.get("sources", []):
        sources.append(SMBSource(
            host=src["host"],
            share=src["share"],
            username=src["username"],
            password=src["password"],
            subfolder=src.get("subfolder", "/"),
            label=src.get("label", src["share"]),
        ))
    return sources


def add_source(host: str, share: str, username: str, password: str,
               subfolder: str = "/", label: str = "") -> dict:
    """Add a new SMB source to the config."""
    config = load_config() or {"sources": []}

    # Check for duplicates
    source_id = f"{host}/{share}{subfolder}".rstrip("/")
    for src in config["sources"]:
        existing_id = f"{src['host']}/{src['share']}{src.get('subfolder', '/')}".rstrip("/")
        if existing_id == source_id:
            return {"success": False, "message": f"Source already exists: {source_id}"}

    new_source = {
        "host": host,
        "share": share,
        "username": username,
        "password": password,
        "subfolder": subfolder,
        "label": label or share,
    }
    config["sources"].append(new_source)
    save_config(config)

    # Register the SMB session
    source = SMBSource(**new_source)
    try:
        register_source(source)
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {e}"}

    return {"success": True, "message": f"Added source: {label or share}", "source_id": source_id}


def remove_source(source_id: str) -> dict:
    """Remove an SMB source from the config and purge its indexed data from the DB."""
    config = load_config()
    if not config:
        return {"success": False, "message": "No config found"}

    # Find the source being removed so we know its label
    removed_label = None
    original_count = len(config.get("sources", []))
    kept = []
    for src in config["sources"]:
        sid = f"{src['host']}/{src['share']}{src.get('subfolder', '/')}".rstrip("/")
        if sid == source_id:
            removed_label = src.get("label", src["share"])
        else:
            kept.append(src)

    if len(kept) == original_count:
        return {"success": False, "message": "Source not found"}

    config["sources"] = kept
    save_config(config)

    # Purge indexed files for this source from the database
    purged = 0
    if removed_label:
        try:
            conn = get_connection()
            prefix = f"/{removed_label}/%"
            root_path = f"/{removed_label}"

            # Delete tags and metadata for files under this source
            conn.execute(
                "DELETE FROM file_tags WHERE file_id IN "
                "(SELECT id FROM files WHERE path LIKE ? OR path = ?)",
                (prefix, root_path)
            )
            conn.execute(
                "DELETE FROM file_metadata WHERE file_id IN "
                "(SELECT id FROM files WHERE path LIKE ? OR path = ?)",
                (prefix, root_path)
            )

            # Delete the files themselves
            cursor = conn.execute(
                "DELETE FROM files WHERE path LIKE ? OR path = ?",
                (prefix, root_path)
            )
            purged = cursor.rowcount
            conn.commit()
            logger.info(f"Purged {purged} indexed entries for source '{removed_label}'")
        except Exception as e:
            logger.warning(f"Failed to purge DB entries for {removed_label}: {e}")

    return {
        "success": True,
        "message": f"Removed source: {source_id}",
        "purged_files": purged,
    }


def register_all_sources():
    """Register SMB sessions for all configured sources. Called on startup."""
    sources = get_sources()
    registered = 0
    for source in sources:
        try:
            register_source(source)
            registered += 1
        except Exception as e:
            logger.warning(f"Failed to register source {source.source_id}: {e}")
    logger.info(f"Registered {registered}/{len(sources)} SMB sources")
    return registered


# ─── Status ───────────────────────────────────────────────────────────────

def get_connection_status() -> dict:
    """Get current NAS connection status for the frontend."""
    config = load_config()
    if not config or not config.get("sources"):
        return {
            "configured": False,
            "connected": False,
            "sources": [],
        }

    sources = []
    any_connected = False

    for src in config["sources"]:
        source = SMBSource(
            host=src["host"],
            share=src["share"],
            username=src["username"],
            password=src["password"],
            subfolder=src.get("subfolder", "/"),
            label=src.get("label", src["share"]),
        )

        # Test if source is reachable
        connected = False
        try:
            result = test_connection(source.host, source.share, source.username, source.password)
            connected = result["success"]
            if connected:
                any_connected = True
        except Exception:
            pass

        sources.append({
            "host": src["host"],
            "share": src["share"],
            "label": src.get("label", src["share"]),
            "subfolder": src.get("subfolder", "/"),
            "connected": connected,
            "source_id": source.source_id,
        })

    return {
        "configured": True,
        "connected": any_connected,
        "sources": sources,
    }
