"""Tests for card reconciliation logic."""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import Card, CardSource, CardStatus, Session
from services.card_reconciler import CardReconciler
from storage import storage


@pytest.fixture
def reconciler():
    return CardReconciler()


def test_derive_title_from_path(reconciler):
    session = Session(
        id="test-123",
        project_path="/Users/user/projects/my-cool-app",
    )
    title = reconciler._derive_title(session)
    assert title == "my-cool-app"


def test_derive_title_no_path(reconciler):
    session = Session(id="abcdef12", project_path="")
    title = reconciler._derive_title(session)
    assert title == "Session abcdef12"


def test_map_status(reconciler):
    assert reconciler._map_status("active") == CardStatus.IN_PROGRESS
    assert reconciler._map_status("waiting") == CardStatus.WAITING
    assert reconciler._map_status("unknown") == CardStatus.BACKLOG


@pytest.mark.asyncio
async def test_reconcile_new_session(reconciler):
    session = Session(
        id="reconcile-test-001",
        project_path="/Users/test/projects/new-project",
        status="active",
        last_activity=datetime.now(timezone.utc),
        source=CardSource.LOCAL,
    )
    changes = await reconciler.reconcile([session])
    assert len(changes) == 1
    assert changes[0].session_id == "reconcile-test-001"
    assert changes[0].title == "new-project"
