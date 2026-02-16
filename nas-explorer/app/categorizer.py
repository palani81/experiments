"""Rule-based auto-categorization engine."""

import os
from datetime import datetime, timezone
from pathlib import Path


# ─── Built-in Rules ──────────────────────────────────────────────────────

# Extension-based categories
EXTENSION_CATEGORIES = {
    # Video
    ".mp4": ["media", "video"],
    ".mkv": ["media", "video"],
    ".avi": ["media", "video"],
    ".mov": ["media", "video"],
    ".wmv": ["media", "video"],
    ".flv": ["media", "video"],
    ".webm": ["media", "video"],
    ".m4v": ["media", "video"],
    ".ts": ["media", "video"],
    ".mpg": ["media", "video"],
    ".mpeg": ["media", "video"],

    # Audio
    ".mp3": ["media", "audio", "music"],
    ".flac": ["media", "audio", "music"],
    ".wav": ["media", "audio"],
    ".aac": ["media", "audio", "music"],
    ".ogg": ["media", "audio"],
    ".wma": ["media", "audio"],
    ".m4a": ["media", "audio", "music"],
    ".opus": ["media", "audio"],
    ".aiff": ["media", "audio"],

    # Images
    ".jpg": ["media", "image", "photo"],
    ".jpeg": ["media", "image", "photo"],
    ".png": ["media", "image"],
    ".gif": ["media", "image"],
    ".bmp": ["media", "image"],
    ".tiff": ["media", "image"],
    ".tif": ["media", "image"],
    ".webp": ["media", "image"],
    ".svg": ["media", "image", "vector"],
    ".raw": ["media", "image", "photo"],
    ".cr2": ["media", "image", "photo"],
    ".nef": ["media", "image", "photo"],
    ".arw": ["media", "image", "photo"],
    ".heic": ["media", "image", "photo"],
    ".heif": ["media", "image", "photo"],

    # Documents
    ".pdf": ["document"],
    ".doc": ["document"],
    ".docx": ["document"],
    ".odt": ["document"],
    ".rtf": ["document"],
    ".txt": ["document", "text"],
    ".md": ["document", "text"],
    ".tex": ["document"],
    ".epub": ["document", "ebook"],

    # Spreadsheets
    ".xlsx": ["document", "spreadsheet"],
    ".xls": ["document", "spreadsheet"],
    ".csv": ["document", "data"],
    ".tsv": ["document", "data"],
    ".ods": ["document", "spreadsheet"],

    # Presentations
    ".pptx": ["document", "presentation"],
    ".ppt": ["document", "presentation"],
    ".odp": ["document", "presentation"],
    ".key": ["document", "presentation"],

    # Code
    ".py": ["code", "python"],
    ".js": ["code", "javascript"],
    ".ts": ["code", "typescript"],
    ".jsx": ["code", "javascript"],
    ".tsx": ["code", "typescript"],
    ".html": ["code", "web"],
    ".css": ["code", "web"],
    ".java": ["code", "java"],
    ".cpp": ["code", "cpp"],
    ".c": ["code", "c"],
    ".h": ["code", "c"],
    ".go": ["code", "go"],
    ".rs": ["code", "rust"],
    ".rb": ["code", "ruby"],
    ".php": ["code", "php"],
    ".swift": ["code", "swift"],
    ".kt": ["code", "kotlin"],
    ".sh": ["code", "shell"],
    ".bash": ["code", "shell"],
    ".sql": ["code", "database"],
    ".r": ["code", "r"],
    ".m": ["code", "matlab"],

    # Archives
    ".zip": ["archive"],
    ".tar": ["archive"],
    ".gz": ["archive"],
    ".bz2": ["archive"],
    ".xz": ["archive"],
    ".7z": ["archive"],
    ".rar": ["archive"],
    ".iso": ["archive", "disk-image"],
    ".dmg": ["archive", "disk-image"],

    # Data
    ".json": ["data"],
    ".xml": ["data"],
    ".yaml": ["data"],
    ".yml": ["data"],
    ".toml": ["data"],
    ".ini": ["data", "config"],
    ".cfg": ["data", "config"],
    ".conf": ["data", "config"],
    ".db": ["data", "database"],
    ".sqlite": ["data", "database"],
    ".sqlite3": ["data", "database"],

    # Fonts
    ".ttf": ["font"],
    ".otf": ["font"],
    ".woff": ["font"],
    ".woff2": ["font"],

    # Subtitles
    ".srt": ["subtitle"],
    ".vtt": ["subtitle"],
    ".ass": ["subtitle"],
    ".ssa": ["subtitle"],
    ".sub": ["subtitle"],

    # 3D / Design
    ".psd": ["design", "photoshop"],
    ".ai": ["design", "illustrator"],
    ".sketch": ["design"],
    ".fig": ["design"],
    ".blend": ["3d"],
    ".obj": ["3d"],
    ".fbx": ["3d"],
    ".stl": ["3d"],

    # Executables / System
    ".exe": ["executable"],
    ".msi": ["executable", "installer"],
    ".deb": ["executable", "installer"],
    ".rpm": ["executable", "installer"],
    ".apk": ["executable", "mobile"],
    ".app": ["executable"],
    ".dll": ["system"],
    ".so": ["system"],
    ".dylib": ["system"],
}

# Size thresholds
SIZE_LARGE_GB = 1
SIZE_HUGE_GB = 10

# Age threshold for "old" tag (days)
OLD_THRESHOLD_DAYS = 365 * 3  # 3 years


def categorize_file(
    filename: str,
    mime_type: str | None,
    size: int,
    modified_at: str | None,
) -> list[str]:
    """
    Apply all categorization rules to a file.
    Returns list of tags.
    """
    tags = set()

    # 1. Extension-based categorization
    ext = Path(filename).suffix.lower()
    if ext in EXTENSION_CATEGORIES:
        tags.update(EXTENSION_CATEGORIES[ext])

    # 2. MIME-based categorization (fallback)
    if mime_type:
        if mime_type.startswith("video/"):
            tags.update(["media", "video"])
        elif mime_type.startswith("audio/"):
            tags.update(["media", "audio"])
        elif mime_type.startswith("image/"):
            tags.update(["media", "image"])
        elif mime_type.startswith("text/"):
            tags.add("text")
        elif mime_type == "application/pdf":
            tags.add("document")

    # 3. Size-based tags
    size_gb = size / (1024 ** 3)
    if size_gb >= SIZE_HUGE_GB:
        tags.update(["huge", "large"])
    elif size_gb >= SIZE_LARGE_GB:
        tags.add("large")
    elif size == 0:
        tags.add("empty")

    # 4. Age-based tags
    if modified_at:
        try:
            mtime = datetime.fromisoformat(modified_at.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - mtime).days
            if age_days > OLD_THRESHOLD_DAYS:
                tags.add("old")
        except (ValueError, TypeError):
            pass

    # 5. Name-based heuristics
    name_lower = filename.lower()

    if name_lower.startswith("."):
        tags.add("hidden")

    if any(kw in name_lower for kw in ("backup", "bak", "old", "copy")):
        tags.add("backup")

    if any(kw in name_lower for kw in ("temp", "tmp", "cache")):
        tags.add("temporary")

    if any(kw in name_lower for kw in ("readme", "changelog", "license", "contributing")):
        tags.add("documentation")

    if any(kw in name_lower for kw in ("screenshot", "screen shot", "capture")):
        tags.add("screenshot")

    return sorted(tags)
