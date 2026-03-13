"""Tests for card CRUD endpoints."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import app
from config import settings

client = TestClient(app)
AUTH_HEADER = {"Authorization": f"Bearer {settings.auth_token}"}


def test_list_cards_empty():
    resp = client.get("/api/cards", headers=AUTH_HEADER)
    assert resp.status_code == 200
    assert "cards" in resp.json()


def test_create_card():
    resp = client.post(
        "/api/cards",
        json={"title": "Test Card", "status": "backlog"},
        headers=AUTH_HEADER,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Card"
    assert data["status"] == "backlog"
    assert "id" in data
    return data["id"]


def test_get_card():
    # Create first
    create_resp = client.post(
        "/api/cards",
        json={"title": "Get Test"},
        headers=AUTH_HEADER,
    )
    card_id = create_resp.json()["id"]

    resp = client.get(f"/api/cards/{card_id}", headers=AUTH_HEADER)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Get Test"


def test_update_card():
    create_resp = client.post(
        "/api/cards",
        json={"title": "Update Test"},
        headers=AUTH_HEADER,
    )
    card_id = create_resp.json()["id"]

    resp = client.patch(
        f"/api/cards/{card_id}",
        json={"status": "in_progress"},
        headers=AUTH_HEADER,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"


def test_delete_card():
    create_resp = client.post(
        "/api/cards",
        json={"title": "Delete Test"},
        headers=AUTH_HEADER,
    )
    card_id = create_resp.json()["id"]

    resp = client.delete(f"/api/cards/{card_id}", headers=AUTH_HEADER)
    assert resp.status_code == 204

    resp = client.get(f"/api/cards/{card_id}", headers=AUTH_HEADER)
    assert resp.status_code == 404


def test_unauthorized():
    resp = client.get("/api/cards", headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 401


def test_filter_by_status():
    client.post(
        "/api/cards",
        json={"title": "Backlog Card", "status": "backlog"},
        headers=AUTH_HEADER,
    )
    client.post(
        "/api/cards",
        json={"title": "Done Card", "status": "done"},
        headers=AUTH_HEADER,
    )

    resp = client.get("/api/cards?status=done", headers=AUTH_HEADER)
    assert resp.status_code == 200
    cards = resp.json()["cards"]
    for card in cards:
        assert card["status"] == "done"
