"""Two-way communication: send replies from phone to Claude Code sessions."""

from __future__ import annotations

import asyncio
import json
import shutil
from typing import Optional


async def start_new_session(project_path: str, prompt: str) -> Optional[str]:
    """Start a new Claude Code session in the given project directory.

    Returns the session ID if successful, None otherwise.
    """
    claude_path = shutil.which("claude")
    if not claude_path:
        return None

    try:
        proc = await asyncio.create_subprocess_exec(
            claude_path,
            "-p", prompt,
            "--yes",
            "--output-format", "json",
            cwd=project_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=300)
        if proc.returncode == 0 and stdout:
            try:
                result = json.loads(stdout.decode())
                return result.get("session_id")
            except (json.JSONDecodeError, KeyError):
                pass
    except (asyncio.TimeoutError, Exception):
        pass

    return None


async def start_new_session_background(project_path: str, prompt: str) -> None:
    """Start a new Claude Code session in the background (fire and forget).

    The session will be discovered by the session monitor once it creates
    its JSONL file.
    """
    claude_path = shutil.which("claude")
    if not claude_path:
        raise RuntimeError("claude CLI not found on PATH")

    await asyncio.create_subprocess_exec(
        claude_path,
        "-p", prompt,
        "--yes",
        cwd=project_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )


async def send_reply_to_session(session_id: str, message: str) -> bool:
    """Send a reply message to an active Claude Code session.

    Tries approaches in order:
    1. claude --resume (CLI approach)
    2. tmux send-keys (if session runs in tmux)

    Returns True if the reply was sent successfully.
    """
    # Approach 1: CLI resume
    if await _try_cli_resume(session_id, message):
        return True

    # Approach 2: tmux fallback
    if await _try_tmux_input(session_id, message):
        return True

    return False


async def _try_cli_resume(session_id: str, message: str) -> bool:
    """Try sending input via claude --resume."""
    claude_path = shutil.which("claude")
    if not claude_path:
        return False

    try:
        proc = await asyncio.create_subprocess_exec(
            claude_path,
            "--resume", session_id,
            "--yes",
            "-p", message,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        return proc.returncode == 0
    except (asyncio.TimeoutError, Exception):
        return False


async def _try_tmux_input(session_id: str, message: str) -> bool:
    """Try sending input via tmux send-keys."""
    tmux_path = shutil.which("tmux")
    if not tmux_path:
        return False

    # Look for a tmux session matching the Claude session ID
    try:
        # List tmux sessions
        proc = await asyncio.create_subprocess_exec(
            tmux_path, "list-sessions", "-F", "#{session_name}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode != 0:
            return False

        session_names = stdout.decode().strip().split("\n")
        target = None
        for name in session_names:
            if session_id[:8] in name or session_id in name:
                target = name
                break

        if not target:
            return False

        # Send keys to the tmux session
        proc = await asyncio.create_subprocess_exec(
            tmux_path, "send-keys", "-t", target, message, "Enter",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0
    except Exception:
        return False
