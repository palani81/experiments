import hashlib
import hmac
import json
import time

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

TOKEN_COOKIE = "kc_session"
TOKEN_MAX_AGE = 60 * 60 * 24 * 30  # 30 days


def _make_token(timestamp: int) -> str:
    """Create an HMAC token tied to the secret key and timestamp."""
    msg = f"{timestamp}".encode()
    sig = hmac.new(settings.secret_key.encode(), msg, hashlib.sha256).hexdigest()
    return f"{timestamp}.{sig}"


def _verify_token(token: str) -> bool:
    """Verify a session token is valid and not expired."""
    try:
        ts_str, sig = token.split(".", 1)
        timestamp = int(ts_str)
    except (ValueError, AttributeError):
        return False
    if time.time() - timestamp > TOKEN_MAX_AGE:
        return False
    expected = _make_token(timestamp)
    return hmac.compare_digest(token, expected)


def verify_password(password: str) -> bool:
    """Constant-time password comparison."""
    return hmac.compare_digest(password.encode(), settings.app_password.encode())


# Paths that don't require auth
PUBLIC_PATHS = {"/api/health", "/login", "/logout"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth if no password is configured
        if not settings.app_password:
            return await call_next(request)

        path = request.url.path

        # Allow public paths
        if path in PUBLIC_PATHS:
            return await call_next(request)

        # Check session cookie
        token = request.cookies.get(TOKEN_COOKIE)
        if token and _verify_token(token):
            return await call_next(request)

        # Not authenticated
        if path.startswith("/api/"):
            return JSONResponse({"detail": "Authentication required"}, status_code=401)

        # Redirect to login for page requests
        return RedirectResponse("/login", status_code=303)


LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Login - Kindle Crossword</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #1a1a2e; min-height: 100vh; display: flex; align-items: center;
    justify-content: center; padding: 20px;
  }
  .card {
    background: #fff; border-radius: 16px; padding: 40px 32px; width: 100%;
    max-width: 380px; box-shadow: 0 8px 32px rgba(0,0,0,.2);
  }
  h1 { font-size: 22px; text-align: center; margin-bottom: 8px; color: #222; }
  .sub { text-align: center; color: #888; font-size: 14px; margin-bottom: 28px; }
  label { display: block; font-size: 13px; color: #555; margin-bottom: 6px; }
  input[type=password] {
    width: 100%; padding: 12px 14px; border: 1px solid #ddd; border-radius: 8px;
    font-size: 16px; outline: none; margin-bottom: 20px;
  }
  input[type=password]:focus { border-color: #4a6cf7; }
  button {
    width: 100%; padding: 12px; border: none; border-radius: 8px; background: #4a6cf7;
    color: #fff; font-size: 16px; font-weight: 500; cursor: pointer;
  }
  button:hover { background: #3b5de7; }
  .error { color: #d32f2f; font-size: 13px; text-align: center; margin-top: 12px; }
</style>
</head>
<body>
<div class="card">
  <h1>Kindle Crossword</h1>
  <p class="sub">Enter your password to continue</p>
  <form method="POST" action="/login">
    <label for="password">Password</label>
    <input type="password" id="password" name="password" autofocus required>
    <button type="submit">Sign in</button>
  </form>
  {error}
</div>
</body>
</html>"""
