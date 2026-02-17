"""Tests for the scanner module (state management, cancellation, helpers)."""

import pytest
import threading
from app.scanner import (
    get_scan_state, stop_scan, _scan_state, _scan_lock, _cancel_event, _is_cancelled,
)


class TestScanState:
    def setup_method(self):
        """Reset scan state before each test."""
        _cancel_event.clear()
        with _scan_lock:
            _scan_state.update({
                "running": False,
                "scan_id": None,
                "phase": "",
                "files_scanned": 0,
                "files_added": 0,
                "files_updated": 0,
                "files_removed": 0,
                "files_enriched": 0,
                "files_to_enrich": 0,
                "errors": 0,
                "total_estimate": 0,
                "current_source": "",
                "started_at": None,
                "error_log": [],
            })

    def test_initial_state(self):
        state = get_scan_state()
        assert state["running"] is False
        assert state["phase"] == ""
        assert state["files_scanned"] == 0
        assert state["files_enriched"] == 0
        assert state["files_to_enrich"] == 0
        assert state["errors"] == 0

    def test_state_is_copy(self):
        """get_scan_state should return a copy, not a reference."""
        state = get_scan_state()
        state["running"] = True
        # Original should be unchanged
        assert get_scan_state()["running"] is False

    def test_state_thread_safety(self):
        """Multiple threads reading state shouldn't crash."""
        results = []

        def reader():
            for _ in range(100):
                s = get_scan_state()
                results.append(s["running"])

        threads = [threading.Thread(target=reader) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(results) == 1000

    def test_phase_tracking(self):
        with _scan_lock:
            _scan_state["running"] = True
            _scan_state["phase"] = "indexing"

        state = get_scan_state()
        assert state["phase"] == "indexing"

        with _scan_lock:
            _scan_state["phase"] = "enriching"
            _scan_state["files_to_enrich"] = 200
            _scan_state["files_enriched"] = 50

        state = get_scan_state()
        assert state["phase"] == "enriching"
        assert state["files_to_enrich"] == 200
        assert state["files_enriched"] == 50

    def test_error_tracking(self):
        with _scan_lock:
            _scan_state["errors"] = 5
            _scan_state["error_log"] = ["err1", "err2", "err3", "err4", "err5"]

        state = get_scan_state()
        assert state["errors"] == 5
        assert len(state["error_log"]) == 5


class TestStopScan:
    def setup_method(self):
        _cancel_event.clear()
        with _scan_lock:
            _scan_state["running"] = False

    def test_stop_when_not_running(self):
        result = stop_scan()
        assert result["success"] is True
        assert "No scan running" in result["message"]
        assert not _cancel_event.is_set()

    def test_stop_when_running(self):
        with _scan_lock:
            _scan_state["running"] = True
        result = stop_scan()
        assert result["success"] is True
        assert _cancel_event.is_set()

    def test_cancel_event_detected(self):
        assert _is_cancelled() is False
        _cancel_event.set()
        assert _is_cancelled() is True
        _cancel_event.clear()
        assert _is_cancelled() is False


class TestScanStateFields:
    """Ensure all expected fields exist in scan state."""

    def test_all_fields_present(self):
        state = get_scan_state()
        expected_fields = [
            "running", "scan_id", "phase",
            "files_scanned", "files_added", "files_updated", "files_removed",
            "files_enriched", "files_to_enrich",
            "errors", "total_estimate", "current_source",
            "started_at", "error_log",
        ]
        for field in expected_fields:
            assert field in state, f"Missing field: {field}"

    def test_counters_are_integers(self):
        state = get_scan_state()
        int_fields = [
            "files_scanned", "files_added", "files_updated", "files_removed",
            "files_enriched", "files_to_enrich", "errors", "total_estimate",
        ]
        for field in int_fields:
            assert isinstance(state[field], int), f"{field} should be int"

    def test_error_log_is_list(self):
        state = get_scan_state()
        assert isinstance(state["error_log"], list)
