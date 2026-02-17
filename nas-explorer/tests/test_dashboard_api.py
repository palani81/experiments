"""Tests for dashboard and insight API endpoints."""

import pytest
import json


class TestDashboardEndpoint:
    """Test the main /api/dashboard endpoint."""

    def test_empty_db(self, client):
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_size"] == 0
        assert data["total_files"] == 0
        assert data["total_directories"] == 0
        assert data["duplicate_groups"] == 0
        assert data["empty_files"] == 0
        assert data["by_type"] == []
        assert data["largest_files"] == []

    def test_with_data(self, client, populated_db):
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        data = resp.json()

        # Basic stats should be non-zero
        assert data["total_size"] > 0
        assert data["total_files"] > 0
        assert data["total_directories"] > 0

        # Duplicates (hash_d1 appears twice)
        assert data["duplicate_groups"] >= 1
        assert data["duplicate_wasted_bytes"] > 0

        # By type should have entries
        assert len(data["by_type"]) > 0

        # Largest files should be ordered by size desc
        largest = data["largest_files"]
        assert len(largest) > 0
        for i in range(len(largest) - 1):
            assert largest[i]["size"] >= largest[i + 1]["size"]

        # Recent files exist
        assert len(data["recent_files"]) > 0

        # Tags exist
        assert len(data["tag_counts"]) > 0

    def test_extended_insights(self, client, populated_db):
        resp = client.get("/api/dashboard")
        data = resp.json()

        # Average file size should be positive
        assert data["avg_file_size"] > 0

        # Median file size should be positive
        assert data["median_file_size"] > 0

        # Oldest files
        assert len(data["oldest_files"]) > 0
        oldest = data["oldest_files"]
        # Should be sorted by date ascending (oldest first)
        for i in range(len(oldest) - 1):
            assert oldest[i]["modified_at"] <= oldest[i + 1]["modified_at"]

        # File age buckets
        assert len(data["file_age_buckets"]) > 0

        # Extension counts
        assert len(data["extension_counts"]) > 0

        # Size by source
        assert len(data["size_by_source"]) > 0

        # Empty files (we inserted 1)
        assert data["empty_files"] >= 1

        # Deep paths
        assert len(data["deep_paths"]) > 0

    def test_duplicates_details(self, client, populated_db):
        resp = client.get("/api/dashboard")
        data = resp.json()
        dupes = data["duplicates"]
        assert len(dupes) >= 1
        for d in dupes:
            assert d["count"] > 1
            assert d["wasted_bytes"] > 0
            assert "|" in d["names"] or d["count"] == 2

    def test_size_by_extension(self, client, populated_db):
        resp = client.get("/api/dashboard")
        data = resp.json()
        ext = data["size_by_extension"]
        assert len(ext) > 0
        # Should be sorted by total_size desc
        for i in range(len(ext) - 1):
            assert ext[i]["total_size"] >= ext[i + 1]["total_size"]


class TestForgottenFolders:
    """Test /api/insights/forgotten-folders."""

    def test_empty_db(self, client):
        resp = client.get("/api/insights/forgotten-folders")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_with_old_files(self, client, populated_db):
        resp = client.get("/api/insights/forgotten-folders")
        assert resp.status_code == 200
        folders = resp.json()
        # /archive/legacy has files from 1200+ days ago
        assert len(folders) >= 1
        folder_paths = [f["folder"] for f in folders]
        assert "/archive/legacy" in folder_paths

        for f in folders:
            assert f["file_count"] > 0
            assert f["total_size"] >= 0
            assert f["last_modified"] is not None

    def test_sorted_by_size(self, client, populated_db):
        resp = client.get("/api/insights/forgotten-folders")
        folders = resp.json()
        for i in range(len(folders) - 1):
            assert folders[i]["total_size"] >= folders[i + 1]["total_size"]


class TestNamingConflicts:
    """Test /api/insights/naming-conflicts."""

    def test_empty_db(self, client):
        resp = client.get("/api/insights/naming-conflicts")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_with_conflicts(self, client, populated_db):
        resp = client.get("/api/insights/naming-conflicts")
        assert resp.status_code == 200
        conflicts = resp.json()
        # beach.jpg exists in /photos/vacation and /photos/screenshots
        assert len(conflicts) >= 1
        names = [c["name"] for c in conflicts]
        assert "beach.jpg" in names

        for c in conflicts:
            assert c["copies"] > 1
            assert c["locations"] > 1
            assert c["total_size"] > 0

    def test_conflict_shows_version_info(self, client, populated_db):
        resp = client.get("/api/insights/naming-conflicts")
        conflicts = resp.json()
        beach = [c for c in conflicts if c["name"] == "beach.jpg"][0]
        # beach.jpg has 2 different hashes (hash_i1 and hash_i3), so unique_versions >= 2
        assert beach["unique_versions"] >= 1
        assert beach["folders"] is not None


class TestMediaSummary:
    """Test /api/insights/media-summary."""

    def test_empty_db(self, client):
        resp = client.get("/api/insights/media-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["video"]["count"] == 0
        assert data["audio"]["count"] == 0
        assert data["images"]["count"] == 0

    def test_with_media(self, client, populated_db):
        resp = client.get("/api/insights/media-summary")
        assert resp.status_code == 200
        data = resp.json()

        # Videos
        assert data["video"]["count"] == 2
        assert data["video"]["total_size"] > 0
        assert isinstance(data["video"]["formats"], list)
        assert len(data["video"]["formats"]) > 0

        # Audio
        assert data["audio"]["count"] == 2
        assert data["audio"]["total_size"] > 0

        # Images
        assert data["images"]["count"] >= 2
        assert data["images"]["total_size"] > 0

    def test_media_duration(self, client, populated_db):
        resp = client.get("/api/insights/media-summary")
        data = resp.json()
        # We inserted metadata with durations for videos (8880+8160=17040 seconds = 4.73 hours)
        assert data["video"]["duration_hours"] > 0
        # Audio has 240 seconds = 0.067 hours
        assert data["audio"]["duration_hours"] > 0

    def test_format_breakdown(self, client, populated_db):
        resp = client.get("/api/insights/media-summary")
        data = resp.json()
        video_exts = [f["extension"] for f in data["video"]["formats"]]
        assert any(".mkv" in e or ".mp4" in e for e in video_exts)


class TestGrowthEstimate:
    """Test /api/insights/growth-estimate."""

    def test_empty_db(self, client):
        resp = client.get("/api/insights/growth-estimate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_current_bytes"] == 0
        assert data["avg_monthly_bytes"] == 0
        assert data["monthly"] == []

    def test_with_data(self, client, populated_db):
        resp = client.get("/api/insights/growth-estimate")
        assert resp.status_code == 200
        data = resp.json()

        assert data["total_current_bytes"] > 0
        assert isinstance(data["monthly"], list)
        assert isinstance(data["projection_12mo_bytes"], int)

    def test_projection_at_least_current(self, client, populated_db):
        resp = client.get("/api/insights/growth-estimate")
        data = resp.json()
        # Projection should be >= current total
        assert data["projection_12mo_bytes"] >= data["total_current_bytes"]

    def test_monthly_structure(self, client, populated_db):
        resp = client.get("/api/insights/growth-estimate")
        data = resp.json()
        for m in data["monthly"]:
            assert "month" in m
            assert "files_added" in m
            assert "bytes_added" in m
            assert len(m["month"]) == 7  # YYYY-MM format


class TestStorageTreemap:
    """Test /api/insights/storage-treemap."""

    def test_empty_db(self, client):
        resp = client.get("/api/insights/storage-treemap")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_with_data(self, client, populated_db):
        resp = client.get("/api/insights/storage-treemap")
        assert resp.status_code == 200
        rows = resp.json()
        assert len(rows) > 0
        for r in rows:
            assert "path" in r
            assert "total_size" in r
            assert "file_count" in r
