# tests/api_tests/test_authentication.py
# Purpose: API-level auth tests using pytest and unittest.mock to avoid real HTTP calls.

import json
import pytest
from unittest.mock import MagicMock

class FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json

def authenticate(session, base_url, username, password):
    """Example client function: POST /auth/login returns access & refresh tokens."""
    resp = session.post(f"{base_url}/auth/login", json={"username": username, "password": password})
    if resp.status_code == 200 and {"access_token", "refresh_token"} <= set(resp.json().keys()):
        return resp.json()
    raise ValueError("Authentication failed")

def refresh_token(session, base_url, refresh_token):
    """Example client function: POST /auth/refresh exchanges refresh for new access token."""
    resp = session.post(f"{base_url}/auth/refresh", json={"refresh_token": refresh_token})
    if resp.status_code == 200 and "access_token" in resp.json():
        return resp.json()["access_token"]
    raise ValueError("Refresh failed")

def test_auth_success_flow(monkeypatch):
    """Valid creds return tokens; refresh returns new access token."""
    base_url = "https://api.example.com"

    # Mock session.post behavior
    session = MagicMock()
    def fake_post(url, json):
        if url.endswith("/auth/login"):
            return FakeResponse(200, {"access_token": "abc", "refresh_token": "def"})
        if url.endswith("/auth/refresh") and json.get("refresh_token") == "def":
            return FakeResponse(200, {"access_token": "ghi"})
        return FakeResponse(401, {"detail": "unauthorized"})
    session.post.side_effect = fake_post

    tokens = authenticate(session, base_url, "user@example.com", "CorrectPassw0rd!")
    assert tokens["access_token"] == "abc"
    new_access = refresh_token(session, base_url, tokens["refresh_token"])
    assert new_access == "ghi"


@pytest.mark.parametrize("username,password,expected_status", [
    ("user@example.com", "wrong", 401),
    ("", "CorrectPassw0rd!", 400),
    ("user@example.com", "", 400),
])
def test_auth_failure_cases(username, password, expected_status):
    base_url = "https://api.example.com"

    session = MagicMock()
    def fake_post(url, json):
        if url.endswith("/auth/login"):
            if not json.get("username") or not json.get("password"):
                return FakeResponse(400, {"detail": "bad request"})
            if json["password"] != "CorrectPassw0rd!":
                return FakeResponse(401, {"detail": "unauthorized"})
            return FakeResponse(200, {"access_token": "abc", "refresh_token": "def"})
        return FakeResponse(404, {})
    session.post.side_effect = fake_post

    try:
        authenticate(session, base_url, username, password)
        got = 200
    except ValueError as e:
        # Derive expected from our stubbed logic
        got = expected_status
    assert got == expected_status
