"""On-demand preview/thumbnail generation with disk caching.

Supports both local files and SMB files (via temp download).
"""
from __future__ import annotations

import os
import subprocess
import logging
import hashlib
from pathlib import Path
from io import BytesIO

from .config import settings

logger = logging.getLogger("nas_explorer.previews")

SIZES = {
    "small": (200, 200),
    "medium": (400, 400),
    "large": (800, 800),
}


def get_cache_path(file_hash: str, size: str) -> str:
    """Get the disk cache path for a preview."""
    cache_dir = Path(settings.cache_path)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return str(cache_dir / f"{file_hash}_{size}.webp")


def get_preview_smb(smb_path: str, mime_type: str, file_hash: str | None, size: str = "medium") -> str | None:
    """
    Get or generate a preview for a file on SMB.
    Downloads to temp if needed for processing.
    Returns path to cached preview image, or None.
    """
    if size not in SIZES:
        size = "medium"

    if not file_hash:
        file_hash = hashlib.md5(smb_path.encode()).hexdigest()[:16]

    cache_path = get_cache_path(file_hash, size)

    # Check cache first
    if os.path.exists(cache_path):
        return cache_path

    # Need to download and process
    from .smb_fs import download_to_temp, cleanup_temp

    temp_path = None
    try:
        temp_path = download_to_temp(smb_path)
        return get_preview(temp_path, mime_type, file_hash, size)
    except Exception as e:
        logger.warning(f"SMB preview generation failed for {smb_path}: {e}")
        return None
    finally:
        if temp_path:
            cleanup_temp(temp_path)


def get_preview(filepath: str, mime_type: str, file_hash: str | None, size: str = "medium") -> str | None:
    """
    Get or generate a preview for a local file.
    Returns path to cached preview image, or None if not possible.
    """
    if size not in SIZES:
        size = "medium"

    if not file_hash:
        file_hash = hashlib.md5(filepath.encode()).hexdigest()[:16]

    cache_path = get_cache_path(file_hash, size)

    # Check cache
    if os.path.exists(cache_path):
        return cache_path

    # Generate based on MIME type
    try:
        if mime_type and mime_type.startswith("image/"):
            return _generate_image_preview(filepath, cache_path, size)
        elif mime_type and mime_type.startswith("video/"):
            return _generate_video_preview(filepath, cache_path, size)
        elif mime_type == "application/pdf":
            return _generate_pdf_preview(filepath, cache_path, size)
        elif mime_type and mime_type.startswith("audio/"):
            return _generate_audio_preview(filepath, cache_path, size)
    except Exception as e:
        logger.warning(f"Preview generation failed for {filepath}: {e}")

    return None


def _generate_image_preview(filepath: str, cache_path: str, size: str) -> str | None:
    """Generate image thumbnail using PIL."""
    try:
        from PIL import Image

        dimensions = SIZES[size]
        img = Image.open(filepath)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        img.thumbnail(dimensions, Image.LANCZOS)
        img.save(cache_path, "WebP", quality=80)
        img.close()
        return cache_path
    except Exception as e:
        logger.debug(f"Image preview failed: {filepath}: {e}")
        return None


def _generate_video_preview(filepath: str, cache_path: str, size: str) -> str | None:
    """Extract a video frame using ffmpeg."""
    try:
        dimensions = SIZES[size]
        width, height = dimensions

        duration = _get_video_duration(filepath)
        seek_time = max(1, int(duration * 0.1)) if duration > 0 else 5

        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", str(seek_time),
                "-i", filepath,
                "-vframes", "1",
                "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease",
                "-f", "webp",
                cache_path,
            ],
            capture_output=True, timeout=30
        )

        if result.returncode == 0 and os.path.exists(cache_path):
            return cache_path

        return None
    except Exception as e:
        logger.debug(f"Video preview failed: {filepath}: {e}")
        return None


def _generate_pdf_preview(filepath: str, cache_path: str, size: str) -> str | None:
    """Render first page of PDF as an image."""
    try:
        from pdf2image import convert_from_path

        dimensions = SIZES[size]
        images = convert_from_path(
            filepath,
            first_page=1,
            last_page=1,
            size=dimensions,
            fmt="webp",
        )

        if images:
            images[0].save(cache_path, "WebP", quality=80)
            return cache_path

        return None
    except Exception as e:
        logger.debug(f"PDF preview failed: {filepath}: {e}")
        return None


def _generate_audio_preview(filepath: str, cache_path: str, size: str) -> str | None:
    """Extract album art from audio files."""
    try:
        from mutagen import File as MutagenFile
        from PIL import Image

        audio = MutagenFile(filepath)
        if audio is None:
            return None

        art_data = None

        # MP3 (ID3)
        if hasattr(audio, "tags") and audio.tags:
            for key in audio.tags:
                if key.startswith("APIC"):
                    art_data = audio.tags[key].data
                    break

        # MP4/M4A
        if art_data is None and hasattr(audio, "tags") and audio.tags:
            covr = audio.tags.get("covr")
            if covr:
                art_data = bytes(covr[0])

        # FLAC
        if art_data is None and hasattr(audio, "pictures"):
            if audio.pictures:
                art_data = audio.pictures[0].data

        if art_data:
            dimensions = SIZES[size]
            img = Image.open(BytesIO(art_data))
            img = img.convert("RGB")
            img.thumbnail(dimensions, Image.LANCZOS)
            img.save(cache_path, "WebP", quality=80)
            img.close()
            return cache_path

        return None
    except Exception as e:
        logger.debug(f"Audio art extraction failed: {filepath}: {e}")
        return None


def _get_video_duration(filepath: str) -> float:
    """Get video duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                filepath,
            ],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception:
        pass
    return 0.0
