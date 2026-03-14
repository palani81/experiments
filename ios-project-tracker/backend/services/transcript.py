"""Parse Claude Code session .jsonl transcript files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from log_config import get_logger

log = get_logger("transcript")


def parse_transcript(file_path: Path) -> list[dict[str, Any]]:
    """Parse a JSONL session file into a list of conversation entries.

    Claude Code JSONL format:
    - Each line has: type (user/assistant/system), message.role, message.content
    - Content can be a string or list of content blocks
    - System entries (hooks, metadata) are skipped
    """
    conversation: list[dict[str, Any]] = []

    try:
        with open(file_path) as f:
            line_count = 0
            for line in f:
                line_count += 1
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError as e:
                    log.warning(f"Bad JSON at {file_path.name}:{line_count}: {e}")
                    continue

                parsed = _parse_entry(entry)
                if parsed:
                    conversation.append(parsed)
    except Exception as e:
        log.error(f"Failed to read transcript {file_path}: {e}")

    return conversation


def _parse_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a single JSONL entry into a normalized conversation entry."""
    if not isinstance(entry, dict):
        return None

    entry_type = entry.get("type", "")

    # Skip system/metadata entries
    if entry_type in ("system", ""):
        return None

    # Claude Code format: message is nested under "message" key
    message = entry.get("message")
    if isinstance(message, dict):
        role = message.get("role", entry_type)
        content = _extract_content(message.get("content", ""))
        if not content.strip():
            return None
        return {
            "role": role,
            "content": content,
            "timestamp": entry.get("timestamp"),
            "type": entry_type,
        }

    # Fallback: flat format (role + content at top level)
    if "role" in entry:
        content = _extract_content(entry.get("content", ""))
        if not content.strip():
            return None
        return {
            "role": entry["role"],
            "content": content,
            "timestamp": entry.get("timestamp"),
            "type": entry.get("type", "message"),
        }

    # Tool use/result format
    if entry_type in ("tool_use", "tool_result"):
        content = _extract_content(entry.get("content", entry.get("output", "")))
        if not content.strip():
            return None
        return {
            "role": "assistant" if entry_type == "tool_use" else "tool",
            "content": content,
            "timestamp": entry.get("timestamp"),
            "type": entry_type,
            "tool_name": entry.get("name", ""),
        }

    return None


def _extract_content(content: Any) -> str:
    """Extract text content from various content formats."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type", "")
                if item_type == "text":
                    parts.append(item.get("text", ""))
                elif item_type == "tool_use":
                    parts.append(f"[Tool: {item.get('name', 'unknown')}]")
                elif item_type == "tool_result":
                    parts.append(f"[Result: {_extract_content(item.get('content', ''))}]")
                # Skip thinking blocks, signatures, etc.
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    if isinstance(content, dict):
        if "text" in content:
            return content["text"]
        return str(content)
    return str(content) if content else ""
