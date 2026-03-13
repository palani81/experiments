"""Tests for session monitoring service."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.transcript import parse_transcript


def test_parse_empty_transcript():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write("")
        f.flush()
        result = parse_transcript(Path(f.name))
    assert result == []


def test_parse_simple_transcript():
    lines = [
        json.dumps({"role": "user", "content": "Hello"}),
        json.dumps({"role": "assistant", "content": "Hi there!"}),
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write("\n".join(lines))
        f.flush()
        result = parse_transcript(Path(f.name))

    assert len(result) == 2
    assert result[0]["role"] == "user"
    assert result[0]["content"] == "Hello"
    assert result[1]["role"] == "assistant"
    assert result[1]["content"] == "Hi there!"


def test_parse_content_blocks():
    entry = {
        "role": "assistant",
        "content": [
            {"type": "text", "text": "Let me help."},
            {"type": "tool_use", "name": "read_file"},
        ],
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write(json.dumps(entry))
        f.flush()
        result = parse_transcript(Path(f.name))

    assert len(result) == 1
    assert "Let me help." in result[0]["content"]
    assert "[Tool: read_file]" in result[0]["content"]


def test_parse_malformed_lines():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write("not json\n")
        f.write(json.dumps({"role": "user", "content": "valid"}) + "\n")
        f.write("also not json\n")
        f.flush()
        result = parse_transcript(Path(f.name))

    assert len(result) == 1
    assert result[0]["content"] == "valid"
