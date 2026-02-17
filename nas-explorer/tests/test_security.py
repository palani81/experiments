"""Tests for security module — auth, path validation."""

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app.security import require_auth, verify_token
from app.config import settings


class TestAuth:
    def test_default_token_allows_unauthenticated(self):
        """When token is the default 'change-me', auth is disabled (dev mode)."""
        original = settings.auth_token
        settings.auth_token = "change-me-to-a-secure-token"
        try:
            app = FastAPI()

            @app.get("/test")
            async def test_endpoint(_=Depends(require_auth)):
                return {"ok": True}

            client = TestClient(app)
            resp = client.get("/test")
            assert resp.status_code == 200
        finally:
            settings.auth_token = original

    def test_custom_token_requires_auth(self):
        original = settings.auth_token
        settings.auth_token = "my-secure-token-123"
        try:
            app = FastAPI()

            @app.get("/test")
            async def test_endpoint(_=Depends(require_auth)):
                return {"ok": True}

            client = TestClient(app)

            # Without token → 401
            resp = client.get("/test")
            assert resp.status_code == 401

            # With wrong token → 401
            resp = client.get("/test", headers={"Authorization": "Bearer wrong-token"})
            assert resp.status_code == 401

            # With correct token → 200
            resp = client.get("/test", headers={"Authorization": "Bearer my-secure-token-123"})
            assert resp.status_code == 200
        finally:
            settings.auth_token = original

    def test_query_param_token_fallback(self):
        original = settings.auth_token
        settings.auth_token = "token-456"
        try:
            app = FastAPI()

            @app.get("/preview")
            async def preview(_=Depends(require_auth)):
                return {"ok": True}

            client = TestClient(app)
            # Token in query param (for img src URLs)
            resp = client.get("/preview?token=token-456")
            assert resp.status_code == 200

            # Wrong query param token
            resp = client.get("/preview?token=wrong")
            assert resp.status_code == 401
        finally:
            settings.auth_token = original
