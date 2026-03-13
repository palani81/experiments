"""Parse Claude Code session .jsonl transcript files."""

import json
from pathlib import Path
from typing import Any


def parse_transcript(file_path: Path) -> list[dict[str, Any]]:
    """Parse a JSONL session file into a list of conversation entries.

    Each entry has: role, content, timestamp (if available), and type.
    """
    conversation: list[dict[str, Any]] = []

    try:
        with open(file_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Handle different entry formats
                parsed = _parse_entry(entry)
                if parsed:
                    conversation.append(parsed)
    except Exception:
        pass

    return conversation


def _parse_entry(entry: dict[str, Any]) -> dict[str, Any] | None:
    """Parse a single JSONL entry into a normalized conversation entry."""
    if not isinstance(entry, dict):
        return None

    # Standard message format
    if "role" in entry:
        return {
            "role": entry["role"],
            "content": _extract_content(entry.get("content", "")),
            "timestamp": entry.get("timestamp"),
            "type": entry.get("type", "message"),
        }

    # Tool use format
    if "type" in entry:
        entry_type = entry["type"]
        if entry_type in ("tool_use", "tool_result"):
            return {
                "role": "assistant" if entry_type == "tool_use" else "tool",
                "content": _extract_content(entry.get("content", entry.get("output", ""))),
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
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif item.get("type") == "tool_use":
                    parts.append(f"[Tool: {item.get('name', 'unknown')}]")
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    if isinstance(content, dict):
        return content.get("text", str(content))
    return str(content) if content else ""
