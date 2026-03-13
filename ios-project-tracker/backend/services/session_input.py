"""Two-way communication: send replies from phone to Claude Code sessions."""

import asyncio
import shutil


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
