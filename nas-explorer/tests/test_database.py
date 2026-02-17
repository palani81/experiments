"""Tests for the database module."""

import pytest
from app.database import get_connection, init_db, query, execute, executemany, get_db


class TestInit:
    def test_tables_exist(self, db_conn):
        """All expected tables should exist after init."""
        rows = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = {r[0] for r in rows}
        assert "files" in table_names
        assert "file_metadata" in table_names
        assert "file_tags" in table_names
        assert "scan_log" in table_names
        assert "files_fts" in table_names

    def test_indexes_exist(self, db_conn):
        rows = db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        ).fetchall()
        idx_names = {r[0] for r in rows}
        assert "idx_files_parent" in idx_names
        assert "idx_files_hash" in idx_names
        assert "idx_files_name" in idx_names
        assert "idx_tags_tag" in idx_names

    def test_wal_mode(self, db_conn):
        result = db_conn.execute("PRAGMA journal_mode").fetchone()
        assert result[0] == "wal"

    def test_foreign_keys_on(self, db_conn):
        result = db_conn.execute("PRAGMA foreign_keys").fetchone()
        assert result[0] == 1


class TestCRUD:
    def test_insert_and_query(self, db_conn):
        execute(
            "INSERT INTO files (path, name, is_directory, size, mime_type) VALUES (?, ?, ?, ?, ?)",
            ("/test/file.txt", "file.txt", 0, 1234, "text/plain")
        )
        rows = query("SELECT * FROM files WHERE path = ?", ("/test/file.txt",))
        assert len(rows) == 1
        assert rows[0]["name"] == "file.txt"
        assert rows[0]["size"] == 1234

    def test_executemany(self, db_conn):
        data = [
            ("/a.txt", "a.txt", 0, 100, "text/plain"),
            ("/b.txt", "b.txt", 0, 200, "text/plain"),
            ("/c.txt", "c.txt", 0, 300, "text/plain"),
        ]
        executemany(
            "INSERT INTO files (path, name, is_directory, size, mime_type) VALUES (?, ?, ?, ?, ?)",
            data
        )
        rows = query("SELECT COUNT(*) as cnt FROM files")
        assert rows[0]["cnt"] == 3

    def test_query_returns_dicts(self, db_conn):
        execute(
            "INSERT INTO files (path, name, is_directory) VALUES (?, ?, ?)",
            ("/dir", "dir", 1)
        )
        rows = query("SELECT * FROM files WHERE path = ?", ("/dir",))
        assert isinstance(rows[0], dict)
        assert "path" in rows[0]

    def test_execute_returns_lastrowid(self, db_conn):
        rid = execute(
            "INSERT INTO files (path, name, is_directory) VALUES (?, ?, ?)",
            ("/test1", "test1", 0)
        )
        assert rid > 0

    def test_get_db_context_manager_commit(self, db_conn):
        with get_db() as conn:
            conn.execute(
                "INSERT INTO files (path, name, is_directory) VALUES (?, ?, ?)",
                ("/ctx_test", "ctx_test", 0)
            )
        rows = query("SELECT * FROM files WHERE path = ?", ("/ctx_test",))
        assert len(rows) == 1

    def test_get_db_context_manager_rollback(self, db_conn):
        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO files (path, name, is_directory) VALUES (?, ?, ?)",
                    ("/rollback_test", "rollback_test", 0)
                )
                raise ValueError("intentional error")
        except ValueError:
            pass
        rows = query("SELECT * FROM files WHERE path = ?", ("/rollback_test",))
        assert len(rows) == 0


class TestFTS:
    def test_fts_insert_trigger(self, db_conn):
        """FTS index should be updated on insert."""
        execute(
            "INSERT INTO files (path, name, is_directory, full_text) VALUES (?, ?, ?, ?)",
            ("/doc.txt", "doc.txt", 0, "machine learning neural networks")
        )
        rows = query("SELECT * FROM files_fts WHERE files_fts MATCH ?", ("machine learning",))
        assert len(rows) >= 1

    def test_fts_name_search(self, db_conn):
        execute(
            "INSERT INTO files (path, name, is_directory) VALUES (?, ?, ?)",
            ("/important_report.pdf", "important_report.pdf", 0)
        )
        rows = query("SELECT * FROM files_fts WHERE files_fts MATCH ?", ("important",))
        assert len(rows) >= 1

    def test_fts_delete_trigger(self, db_conn):
        fid = execute(
            "INSERT INTO files (path, name, is_directory, full_text) VALUES (?, ?, ?, ?)",
            ("/temp.txt", "temp.txt", 0, "unique_searchterm_xyz")
        )
        execute("DELETE FROM files WHERE id = ?", (fid,))
        rows = query("SELECT * FROM files_fts WHERE files_fts MATCH ?", ("unique_searchterm_xyz",))
        assert len(rows) == 0


class TestTags:
    def test_insert_tag(self, db_conn):
        fid = execute(
            "INSERT INTO files (path, name, is_directory) VALUES (?, ?, ?)",
            ("/tagged.mp4", "tagged.mp4", 0)
        )
        execute("INSERT INTO file_tags (file_id, tag) VALUES (?, ?)", (fid, "video"))
        execute("INSERT INTO file_tags (file_id, tag) VALUES (?, ?)", (fid, "media"))
        rows = query("SELECT tag FROM file_tags WHERE file_id = ?", (fid,))
        tags = {r["tag"] for r in rows}
        assert tags == {"video", "media"}

    def test_unique_tag_constraint(self, db_conn):
        """Duplicate (file_id, tag) should be rejected."""
        fid = execute(
            "INSERT INTO files (path, name, is_directory) VALUES (?, ?, ?)",
            ("/dup_tag.txt", "dup_tag.txt", 0)
        )
        execute("INSERT INTO file_tags (file_id, tag) VALUES (?, ?)", (fid, "test"))
        # INSERT OR IGNORE should silently skip
        db_conn.execute("INSERT OR IGNORE INTO file_tags (file_id, tag) VALUES (?, ?)", (fid, "test"))
        db_conn.commit()
        rows = query("SELECT COUNT(*) as cnt FROM file_tags WHERE file_id = ?", (fid,))
        assert rows[0]["cnt"] == 1


class TestMetadata:
    def test_insert_metadata(self, db_conn):
        import json
        fid = execute(
            "INSERT INTO files (path, name, is_directory) VALUES (?, ?, ?)",
            ("/vid.mp4", "vid.mp4", 0)
        )
        meta = json.dumps({"duration": 120, "resolution": "1920x1080"})
        execute("INSERT INTO file_metadata (file_id, metadata) VALUES (?, ?)", (fid, meta))
        rows = query("SELECT metadata FROM file_metadata WHERE file_id = ?", (fid,))
        assert len(rows) == 1
        parsed = json.loads(rows[0]["metadata"])
        assert parsed["duration"] == 120

    def test_cascade_delete(self, db_conn):
        """Deleting a file should cascade to metadata and tags."""
        fid = execute(
            "INSERT INTO files (path, name, is_directory) VALUES (?, ?, ?)",
            ("/cascade.txt", "cascade.txt", 0)
        )
        execute("INSERT INTO file_tags (file_id, tag) VALUES (?, ?)", (fid, "test"))
        execute("INSERT INTO file_metadata (file_id, metadata) VALUES (?, ?)", (fid, '{}'))
        execute("DELETE FROM files WHERE id = ?", (fid,))
        assert query("SELECT * FROM file_tags WHERE file_id = ?", (fid,)) == []
        assert query("SELECT * FROM file_metadata WHERE file_id = ?", (fid,)) == []
