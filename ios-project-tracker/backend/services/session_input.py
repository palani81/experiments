"""Two-way communication: send replies from phone to Claude Code sessions."""

from __future__ import annotations

import asyncio
import json
import shutil
from typing import Optional

from log_config import get_logger

log = get_logger("session_input")


async def start_new_session(project_path: str, prompt: str) -> Optional[str]:
    """Start a new Claude Code session in the given project directory.

    Returns the session ID if successful, None otherwise.
    """
    claude_path = shutil.which("claude")
    if not claude_path:
        log.error("claude CLI not found on PATH")
        return None

    log.info(f"Starting session (sync) in {project_path}: {prompt[:80]}")
    try:
        proc = await asyncio.create_subprocess_exec(
            claude_path,
            "-p", prompt,
            "--dangerously-skip-permissions",
            "--output-format", "json",
            cwd=project_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
        if proc.returncode == 0 and stdout:
            try:
                result = json.loads(stdout.decode())
                session_id = result.get("session_id")
                log.info(f"Session started successfully: {session_id}")
                return session_id
            except (json.JSONDecodeError, KeyError) as e:
                log.error(f"Failed to parse session response: {e}, stdout={stdout.decode()[:200]}")
        else:
            log.error(f"claude exited with code {proc.returncode}, stderr={stderr.decode()[:300] if stderr else 'none'}")
    except asyncio.TimeoutError:
        log.error(f"Session start timed out after 300s in {project_path}")
    except Exception as e:
        log.error(f"Session start failed: {e}")

    return None


async def start_new_session_background(project_path: str, prompt: str) -> None:
    """Start a new Claude Code session in the background (fire and forget).

    The session will be discovered by the session monitor once it creates
    its JSONL file.
    """
    claude_path = shutil.which("claude")
    if not claude_path:
        log.error("claude CLI not found on PATH — cannot start session")
        raise RuntimeError("claude CLI not found on PATH")

    log.info(f"Starting background session in {project_path}")
    log.info(f"  prompt: {prompt[:120]}")
    log.info(f"  command: {claude_path} -p '...' --dangerously-skip-permissions  cwd={project_path}")

    proc = await asyncio.create_subprocess_exec(
        claude_path,
        "-p", prompt,
        "--dangerously-skip-permissions",
        cwd=project_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    log.info(f"Background session launched (pid={proc.pid})")


async def send_reply_to_session(session_id: str, message: str) -> bool:
    """Send a reply message to an active Claude Code session.

    Tries approaches in order:
    1. claude --resume (CLI approach)
    2. tmux send-keys (if session runs in tmux)

    Returns True if the reply was sent successfully.
    """
    log.info(f"Sending reply to session {session_id[:12]}: {message[:80]}")

    # Approach 1: CLI resume
    if await _try_cli_resume(session_id, message):
        log.info(f"Reply sent via CLI resume to {session_id[:12]}")
        return True

    # Approach 2: tmux fallback
    if await _try_tmux_input(session_id, message):
        log.info(f"Reply sent via tmux to {session_id[:12]}")
        return True

    log.error(f"All reply methods failed for session {session_id[:12]}")
    return False


async def _try_cli_resume(session_id: str, message: str) -> bool:
    """Try sending input via claude --resume."""
    claude_path = shutil.which("claude")
    if not claude_path:
        log.warning("claude CLI not found — cannot resume")
        return False

    try:
        log.info(f"Trying CLI resume for {session_id[:12]}")
        proc = await asyncio.create_subprocess_exec(
            claude_path,
            "--resume", session_id,
            "--dangerously-skip-permissions",
            "-p", message,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        if proc.returncode == 0:
            return True
        log.warning(f"CLI resume failed (exit={proc.returncode}): {stderr.decode()[:200] if stderr else 'no stderr'}")
        return False
    except asyncio.TimeoutError:
        log.error(f"CLI resume timed out for {session_id[:12]}")
        return False
    except Exception as e:
        log.error(f"CLI resume error: {e}")
        return False


async def _try_tmux_input(session_id: str, message: str) -> bool:
    """Try sending input via tmux send-keys."""
    tmux_path = shutil.which("tmux")
    if not tmux_path:
        log.info("tmux not found — skipping tmux fallback")
        return False

    # Look for a tmux session matching the Claude session ID
    try:
        log.info(f"Trying tmux fallback for {session_id[:12]}")
        # List tmux sessions
        proc = await asyncio.create_subprocess_exec(
            tmux_path, "list-sessions", "-F", "#{session_name}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode != 0:
            log.info("No tmux sessions found")
            return False

        session_names = stdout.decode().strip().split("\n")
        target = None
        for name in session_names:
            if session_id[:8] in name or session_id in name:
                target = name
                break

        if not target:
            log.info(f"No tmux session matches {session_id[:12]}")
            return False

        # Send keys to the tmux session
        log.info(f"Sending to tmux session: {target}")
        proc = await asyncio.create_subprocess_exec(
            tmux_path, "send-keys", "-t", target, message, "Enter",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return proc.returncode == 0
    except Exception as e:
        log.error(f"tmux fallback failed: {e}")
        return False
