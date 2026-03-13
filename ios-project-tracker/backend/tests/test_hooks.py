"""Tests for hook receiver endpoints."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from storage import storage

client = TestClient(app)


def test_session_start_creates_card():
    resp = client.post(
        "/hooks/session-start",
        json={
            "event_type": "session_start",
            "session_id": "test-session-001",
            "project_path": "/Users/test/projects/myapp",
            "payload": {"title": "My App Session"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["card_id"] is not None

    # Verify card was created
    card = storage.get_card_by_session("test-session-001")
    assert card is not None
    assert card.status.value == "in_progress"


def test_stop_transitions_to_waiting():
    # First create a session
    client.post(
        "/hooks/session-start",
        json={
            "event_type": "session_start",
            "session_id": "test-session-002",
            "project_path": "/Users/test/projects/app2",
            "payload": {},
        },
    )

    # Then stop it
    resp = client.post(
        "/hooks/stop",
        json={
            "event_type": "stop",
            "session_id": "test-session-002",
            "project_path": "/Users/test/projects/app2",
            "payload": {"reason": "needs_input"},
        },
    )
    assert resp.status_code == 200

    card = storage.get_card_by_session("test-session-002")
    assert card is not None
    assert card.status.value == "waiting"


def test_session_end_transitions_to_done():
    client.post(
        "/hooks/session-start",
        json={
            "event_type": "session_start",
            "session_id": "test-session-003",
            "project_path": "/Users/test/projects/app3",
            "payload": {},
        },
    )

    resp = client.post(
        "/hooks/session-end",
        json={
            "event_type": "session_end",
            "session_id": "test-session-003",
            "project_path": "/Users/test/projects/app3",
            "payload": {},
        },
    )
    assert resp.status_code == 200

    card = storage.get_card_by_session("test-session-003")
    assert card.status.value == "done"


def test_notification_hook():
    client.post(
        "/hooks/session-start",
        json={
            "event_type": "session_start",
            "session_id": "test-session-004",
            "project_path": "/Users/test/projects/app4",
            "payload": {},
        },
    )

    resp = client.post(
        "/hooks/notification",
        json={
            "event_type": "notification",
            "session_id": "test-session-004",
            "project_path": "/Users/test/projects/app4",
            "payload": {"message": "Build failed!"},
        },
    )
    assert resp.status_code == 200


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
