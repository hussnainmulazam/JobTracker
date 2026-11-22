"""
Unit test suite verifying Google OAuth configuration and logic for:
1. Recruiter Login / Signup ("Continue with Google")
2. Google Workspace Connection (Settings > Google Workspace)
Runs entirely locally in-memory without remote database calls.
"""
import uuid
import urllib.parse
import pytest
from unittest.mock import MagicMock

from app.core.config import settings
from app.core.security import create_oauth_state, decode_oauth_state
from app.services.auth_service import auth_service
from app.services.google_service import GoogleService, WORKSPACE_SCOPES


def test_login_oauth_url_and_scopes():
    """Verifies that Login OAuth URL uses openid/email/profile scopes and matches Google Cloud Console redirect URI."""
    url = auth_service.get_google_auth_url()
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    # 1. Matches Google Cloud Console Authorized redirect URI
    expected_uris = (
        "http://localhost:8000/auth/google/callback",
        "https://snowiness-reformer-copied.ngrok-free.dev/auth/google/callback",
    )
    assert params["redirect_uri"][0] in expected_uris

    # 2. Scopes are strictly openid, email, profile (no workspace scopes)
    scopes = params["scope"][0].split()
    assert "openid" in scopes
    assert "email" in scopes
    assert "profile" in scopes
    assert not any("gmail" in s or "calendar" in s for s in scopes)

    # 3. State token contains flow='login' and redirect_uri
    state = params["state"][0]
    payload = decode_oauth_state(state)
    assert payload["flow"] == "login"
    assert payload["redirect_uri"] in expected_uris


def test_workspace_oauth_url_and_scopes():
    """Verifies that Workspace OAuth URL requests all 6 Workspace services and matches Google Cloud Console redirect URI."""
    mock_session = MagicMock()
    service = GoogleService(mock_session)
    user_id = uuid.uuid4()

    resp = service.generate_auth_url(user_id)
    assert hasattr(resp, "auth_url")
    assert hasattr(resp, "state")

    parsed = urllib.parse.urlparse(resp.auth_url)
    params = urllib.parse.parse_qs(parsed.query)

    # 1. Matches Google Cloud Console Authorized redirect URI
    expected_uris = (
        "http://localhost:8000/auth/google/callback",
        "https://snowiness-reformer-copied.ngrok-free.dev/auth/google/callback",
    )
    assert params["redirect_uri"][0] in expected_uris

    # 2. State token contains flow='workspace', user_id, and redirect_uri
    payload = decode_oauth_state(resp.state)
    assert payload["flow"] == "workspace"
    assert payload["user_id"] == str(user_id)
    assert payload["redirect_uri"] in expected_uris

    # 3. Scopes contain all 6 required Workspace services
    full_scope_str = params["scope"][0]
    required_services = ["gmail", "calendar", "meetings", "spreadsheets", "documents", "drive"]
    for s in required_services:
        assert s in full_scope_str, f"Required workspace service scope missing: {s}"


def test_dual_flow_state_separation():
    """Verifies that signed state tokens cleanly distinguish login from workspace flows."""
    user_id = str(uuid.uuid4())
    state_login = create_oauth_state(flow="login", extra={"redirect_uri": "http://localhost:8000/auth/google/callback"})
    state_ws = create_oauth_state(flow="workspace", extra={"user_id": user_id, "redirect_uri": "http://localhost:8000/auth/google/callback"})

    decoded_login = decode_oauth_state(state_login)
    decoded_ws = decode_oauth_state(state_ws)

    assert decoded_login["flow"] == "login"
    assert "user_id" not in decoded_login

    assert decoded_ws["flow"] == "workspace"
    assert decoded_ws["user_id"] == user_id
