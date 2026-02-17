"""Tests for Pydantic models."""

import pytest
from app.models import (
    FileItem, FileListResponse, SearchRequest, SearchResponse,
    FolderNode, DashboardData, ScanStatus,
)


class TestFileItem:
    def test_basic_creation(self):
        f = FileItem(id=1, path="/test/file.txt", name="file.txt")
        assert f.id == 1
        assert f.path == "/test/file.txt"
        assert f.name == "file.txt"
        assert f.size == 0
        assert f.tags == []

    def test_from_row(self):
        row = {
            "id": 42, "path": "/media/song.mp3", "name": "song.mp3",
            "parent_path": "/media", "is_directory": 0, "size": 5000000,
            "mime_type": "audio/mpeg", "file_hash": "abc123",
            "created_at": "2024-01-01T00:00:00", "modified_at": "2024-06-01T00:00:00",
            "indexed_at": "2024-06-15T00:00:00",
        }
        f = FileItem.from_row(row, tags=["audio", "music"])
        assert f.id == 42
        assert f.tags == ["audio", "music"]
        assert f.preview_url is None  # audio has no preview

    def test_from_row_preview_url_for_image(self):
        row = {
            "id": 10, "path": "/photos/img.jpg", "name": "img.jpg",
            "mime_type": "image/jpeg", "size": 1000,
        }
        f = FileItem.from_row(row)
        assert f.preview_url is not None
        assert "preview/10" in f.preview_url

    def test_from_row_preview_url_for_video(self):
        row = {
            "id": 11, "path": "/vid/clip.mp4", "name": "clip.mp4",
            "mime_type": "video/mp4", "size": 50000,
        }
        f = FileItem.from_row(row)
        assert f.preview_url is not None

    def test_from_row_preview_url_for_pdf(self):
        row = {
            "id": 12, "path": "/doc/report.pdf", "name": "report.pdf",
            "mime_type": "application/pdf", "size": 1000,
        }
        f = FileItem.from_row(row)
        assert f.preview_url is not None

    def test_from_row_no_preview_for_text(self):
        row = {
            "id": 13, "path": "/doc/notes.txt", "name": "notes.txt",
            "mime_type": "text/plain", "size": 100,
        }
        f = FileItem.from_row(row)
        assert f.preview_url is None

    def test_is_directory_flag(self):
        f = FileItem(id=1, path="/dir", name="dir", is_directory=True)
        assert f.is_directory is True


class TestScanStatus:
    def test_defaults(self):
        s = ScanStatus()
        assert s.status == "idle"
        assert s.phase == ""
        assert s.files_scanned == 0
        assert s.files_enriched == 0
        assert s.files_to_enrich == 0

    def test_with_phase(self):
        s = ScanStatus(
            status="scanning", phase="enriching",
            files_enriched=50, files_to_enrich=200
        )
        assert s.phase == "enriching"
        assert s.files_enriched == 50
        assert s.files_to_enrich == 200

    def test_indexing_phase(self):
        s = ScanStatus(
            status="scanning", phase="indexing",
            files_scanned=100, files_added=80, files_updated=20
        )
        assert s.phase == "indexing"
        assert s.files_scanned == 100


class TestDashboardData:
    def test_defaults(self):
        d = DashboardData()
        assert d.total_size == 0
        assert d.total_files == 0
        assert d.oldest_files == []
        assert d.avg_file_size == 0
        assert d.empty_files == 0
        assert d.deep_paths == []

    def test_populated(self):
        d = DashboardData(
            total_size=1_000_000_000,
            total_files=500,
            avg_file_size=2_000_000,
            median_file_size=500_000,
            empty_files=3,
            deep_paths=[{"path": "/a/b/c/d/e", "depth": 5}],
        )
        assert d.total_size == 1_000_000_000
        assert d.avg_file_size == 2_000_000
        assert len(d.deep_paths) == 1


class TestSearchRequest:
    def test_defaults(self):
        r = SearchRequest(query="test")
        assert r.sort_by == "relevance"
        assert r.limit == 50
        assert r.skip == 0

    def test_custom(self):
        r = SearchRequest(query="*.mp4", mime_type="video/mp4", min_size=1000, limit=10)
        assert r.mime_type == "video/mp4"
        assert r.limit == 10


class TestFileListResponse:
    def test_creation(self):
        r = FileListResponse(items=[], total=0, has_more=False)
        assert r.total == 0
        assert r.has_more is False


class TestFolderNode:
    def test_nested(self):
        child = FolderNode(id=2, name="sub", path="/root/sub", file_count=5)
        parent = FolderNode(id=1, name="root", path="/root", children=[child])
        assert len(parent.children) == 1
        assert parent.children[0].file_count == 5
