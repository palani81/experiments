"""Centralized logging configuration with in-memory ring buffer for /api/logs."""

import logging
import collections
from datetime import datetime, timezone
from typing import Any


class RingBufferHandler(logging.Handler):
    """Stores recent log entries in a ring buffer for the /api/logs endpoint."""

    def __init__(self, capacity: int = 500):
        super().__init__()
        self.buffer: collections.deque[dict[str, Any]] = collections.deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord):
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": self.format(record),
        }
        self.buffer.append(entry)

    def get_logs(self, limit: int = 100, level: str | None = None) -> list[dict]:
        logs = list(self.buffer)
        if level:
            level_upper = level.upper()
            logs = [e for e in logs if e["level"] == level_upper]
        return logs[-limit:]


# Singleton ring buffer handler
ring_handler = RingBufferHandler(capacity=500)
ring_handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))


def setup_logging():
    """Configure logging for the entire application."""
    # Root logger
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Console handler with timestamps
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    ))
    root.addHandler(console)

    # Ring buffer handler (for /api/logs)
    root.addHandler(ring_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger."""
    return logging.getLogger(name)
