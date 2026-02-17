"""Tests for the rule-based auto-categorization engine."""

import pytest
from datetime import datetime, timezone, timedelta
from app.categorizer import categorize_file


class TestExtensionCategories:
    """Test that file extensions are mapped to correct tags."""

    @pytest.mark.parametrize("filename,expected_tags", [
        ("movie.mp4", ["media", "video"]),
        ("movie.mkv", ["media", "video"]),
        ("movie.avi", ["media", "video"]),
        ("song.mp3", ["media", "audio", "music"]),
        ("song.flac", ["media", "audio", "music"]),
        ("track.wav", ["media", "audio"]),
        ("photo.jpg", ["media", "image", "photo"]),
        ("icon.png", ["media", "image"]),
        ("icon.svg", ["media", "image", "vector"]),
        ("shot.heic", ["media", "image", "photo"]),
        ("report.pdf", ["document"]),
        ("essay.docx", ["document"]),
        ("readme.md", ["document", "text"]),
        ("data.xlsx", ["document", "spreadsheet"]),
        ("budget.csv", ["document", "data"]),
        ("slides.pptx", ["document", "presentation"]),
        ("app.py", ["code", "python"]),
        ("index.html", ["code", "web"]),
        ("main.go", ["code", "go"]),
        ("backup.zip", ["archive"]),
        ("disk.iso", ["archive", "disk-image"]),
        ("config.json", ["data"]),
        ("settings.yml", ["data"]),
        ("db.sqlite3", ["data", "database"]),
        ("font.ttf", ["font"]),
        ("captions.srt", ["subtitle"]),
        ("model.blend", ["3d"]),
        ("design.psd", ["design", "photoshop"]),
        ("setup.exe", ["executable"]),
        ("install.deb", ["executable", "installer"]),
    ])
    def test_extension_mapping(self, filename, expected_tags):
        tags = categorize_file(filename, None, 1000, None)
        for expected in expected_tags:
            assert expected in tags, f"Expected '{expected}' in tags for {filename}, got {tags}"

    def test_unknown_extension(self):
        tags = categorize_file("mystery.xyz123", None, 1000, None)
        # Should not crash, may return empty or just size/name based tags
        assert isinstance(tags, list)


class TestMIMEFallback:
    """Test MIME-based categorization when extension isn't mapped."""

    def test_video_mime(self):
        tags = categorize_file("clip.unknown", "video/x-custom", 1000, None)
        assert "video" in tags
        assert "media" in tags

    def test_audio_mime(self):
        tags = categorize_file("track.unknown", "audio/x-custom", 1000, None)
        assert "audio" in tags
        assert "media" in tags

    def test_image_mime(self):
        tags = categorize_file("img.unknown", "image/x-custom", 1000, None)
        assert "image" in tags
        assert "media" in tags

    def test_text_mime(self):
        tags = categorize_file("file.unknown", "text/x-custom", 1000, None)
        assert "text" in tags

    def test_pdf_mime(self):
        tags = categorize_file("file.unknown", "application/pdf", 1000, None)
        assert "document" in tags


class TestSizeTags:
    """Test size-based tagging."""

    def test_huge_file(self):
        size = 15 * 1024**3  # 15 GB
        tags = categorize_file("bigfile.dat", None, size, None)
        assert "huge" in tags
        assert "large" in tags

    def test_large_file(self):
        size = 2 * 1024**3  # 2 GB
        tags = categorize_file("largefile.dat", None, size, None)
        assert "large" in tags
        assert "huge" not in tags

    def test_normal_file(self):
        tags = categorize_file("normal.txt", None, 50_000, None)
        assert "large" not in tags
        assert "huge" not in tags

    def test_empty_file(self):
        tags = categorize_file("empty.txt", None, 0, None)
        assert "empty" in tags


class TestAgeTags:
    """Test age-based tagging."""

    def test_old_file(self):
        old_date = (datetime.now(timezone.utc) - timedelta(days=1200)).isoformat()
        tags = categorize_file("old.txt", None, 100, old_date)
        assert "old" in tags

    def test_recent_file(self):
        recent = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        tags = categorize_file("new.txt", None, 100, recent)
        assert "old" not in tags

    def test_no_date(self):
        tags = categorize_file("nodate.txt", None, 100, None)
        assert "old" not in tags


class TestNameHeuristics:
    """Test filename-based heuristic tagging."""

    def test_hidden_file(self):
        tags = categorize_file(".hidden_config", None, 100, None)
        assert "hidden" in tags

    def test_backup_keywords(self):
        for name in ["backup_2024.tar", "data.bak", "old_version.zip", "file_copy.txt"]:
            tags = categorize_file(name, None, 100, None)
            assert "backup" in tags, f"Expected 'backup' for {name}"

    def test_temp_keywords(self):
        for name in ["tempfile.dat", "cache_data.bin", "tmp_output.txt"]:
            tags = categorize_file(name, None, 100, None)
            assert "temporary" in tags, f"Expected 'temporary' for {name}"

    def test_documentation_keywords(self):
        for name in ["README.md", "CHANGELOG.txt", "LICENSE", "CONTRIBUTING.md"]:
            tags = categorize_file(name, None, 100, None)
            assert "documentation" in tags, f"Expected 'documentation' for {name}"

    def test_screenshot_keywords(self):
        tags = categorize_file("Screenshot_2024.png", None, 100, None)
        assert "screenshot" in tags


class TestCombinedTags:
    """Test that multiple rules can fire together."""

    def test_old_large_video(self):
        old_date = (datetime.now(timezone.utc) - timedelta(days=1500)).isoformat()
        size = 5 * 1024**3
        tags = categorize_file("old_movie.mkv", "video/x-matroska", size, old_date)
        assert "video" in tags
        assert "media" in tags
        assert "old" in tags
        assert "large" in tags

    def test_hidden_backup_archive(self):
        tags = categorize_file(".backup_data.zip", None, 100, None)
        assert "hidden" in tags
        assert "backup" in tags
        assert "archive" in tags

    def test_tags_are_sorted(self):
        tags = categorize_file("song.mp3", "audio/mpeg", 100, None)
        assert tags == sorted(tags)
