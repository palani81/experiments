"""Git/GitHub service for tracking PR status."""

from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path


async def get_pr_for_branch(project_path: str, branch: str) -> dict | None:
    """Check if there's an open PR for the given branch using gh CLI."""
    gh_path = shutil.which("gh")
    if not gh_path or not branch:
        return None

    try:
        proc = await asyncio.create_subprocess_exec(
            gh_path, "pr", "list",
            "--head", branch,
            "--json", "number,title,url,state",
            "--limit", "1",
            cwd=project_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=15)
        if proc.returncode != 0:
            return None

        prs = json.loads(stdout.decode())
        return prs[0] if prs else None
    except Exception:
        return None


async def get_current_branch(project_path: str) -> str | None:
    """Get the current git branch for a project directory."""
    git_path = shutil.which("git")
    if not git_path:
        return None

    try:
        proc = await asyncio.create_subprocess_exec(
            git_path, "rev-parse", "--abbrev-ref", "HEAD",
            cwd=project_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            return stdout.decode().strip()
    except Exception:
        pass
    return None
