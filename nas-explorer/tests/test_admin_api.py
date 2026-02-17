"""Tests for admin API endpoints."""

import pytest
from app.scanner import _scan_state, _scan_lock, _cancel_event


class TestScanStatus:
    def test_idle_status(self, client):
        resp = client.get("/api/admin/scan-status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "idle"
        assert data["files_scanned"] == 0

    def test_status_includes_phase_fields(self, client):
        resp = client.get("/api/admin/scan-status")
        data = resp.json()
        assert "phase" in data
        assert "files_enriched" in data
        assert "files_to_enrich" in data

    def test_status_while_scanning(self, client):
        """Simulate scan state and check status report."""
        with _scan_lock:
            _scan_state["running"] = True
            _scan_state["phase"] = "indexing"
            _scan_state["files_scanned"] = 42
            _scan_state["current_source"] = "media"
        try:
            resp = client.get("/api/admin/scan-status")
            data = resp.json()
            assert data["status"] == "scanning"
            assert data["files_scanned"] == 42
            assert data["current_source"] == "media"
        finally:
            with _scan_lock:
                _scan_state["running"] = False
                _scan_state["phase"] = ""
                _scan_state["files_scanned"] = 0
                _scan_state["current_source"] = ""


class TestScanStop:
    def test_stop_when_idle(self, client):
        resp = client.post("/api/admin/scan-stop")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "No scan running" in data["message"]

    def test_stop_when_scanning(self, client):
        _cancel_event.clear()
        with _scan_lock:
            _scan_state["running"] = True
        try:
            resp = client.post("/api/admin/scan-stop")
            data = resp.json()
            assert data["success"] is True
            assert _cancel_event.is_set()
        finally:
            _cancel_event.clear()
            with _scan_lock:
                _scan_state["running"] = False


class TestScanHistory:
    def test_empty_history(self, client):
        resp = client.get("/api/admin/scan-history")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_history_with_entries(self, client, db_conn):
        from app.database import execute
        execute(
            "INSERT INTO scan_log (started_at, status, files_scanned) VALUES (?, ?, ?)",
            ("2024-01-01T00:00:00", "completed", 500)
        )
        execute(
            "INSERT INTO scan_log (started_at, status, files_scanned) VALUES (?, ?, ?)",
            ("2024-02-01T00:00:00", "completed", 600)
        )
        resp = client.get("/api/admin/scan-history?limit=10")
        assert resp.status_code == 200
        history = resp.json()
        assert len(history) == 2
        # Most recent first
        assert history[0]["files_scanned"] == 600

    def test_history_respects_limit(self, client, db_conn):
        from app.database import execute
        for i in range(5):
            execute(
                "INSERT INTO scan_log (started_at, status) VALUES (?, ?)",
                (f"2024-0{i+1}-01T00:00:00", "completed")
            )
        resp = client.get("/api/admin/scan-history?limit=2")
        assert len(resp.json()) == 2


class TestHealthEndpoint:
    def test_health_no_auth_required(self, isolated_db):
        """Health endpoint should work without auth."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.routes.admin import router

        app = FastAPI()
        # Don't override auth — health shouldn't need it
        app.include_router(router)
        c = TestClient(app)
        resp = c.get("/api/admin/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert "database" in data
        assert "indexed_files" in data

    def test_health_reports_file_count(self, client, populated_db):
        resp = client.get("/api/admin/health")
        data = resp.json()
        assert data["indexed_files"] > 0


class TestTagsEndpoint:
    def test_empty_tags(self, client):
        resp = client.get("/api/admin/tags")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_with_tags(self, client, populated_db):
        resp = client.get("/api/admin/tags")
        assert resp.status_code == 200
        tags = resp.json()
        assert len(tags) > 0
        # Should have counts
        for t in tags:
            assert "tag" in t
            assert "count" in t
            assert t["count"] > 0
        # Media should be the most common tag
        tag_names = [t["tag"] for t in tags]
        assert "media" in tag_names

    def test_tags_sorted_by_count(self, client, populated_db):
        resp = client.get("/api/admin/tags")
        tags = resp.json()
        for i in range(len(tags) - 1):
            assert tags[i]["count"] >= tags[i + 1]["count"]
