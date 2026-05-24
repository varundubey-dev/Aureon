# =========================================================
# OAuth Route Tests
# =========================================================
#
# This file tests ONLY OAuth route behavior:
#
# Covered areas:
#
# 1. Google login route
#    - Redirect initiation
#    - Guest session storage
#
# 2. Google callback route
#    - Missing userinfo redirect
#    - Existing login redirect
#    - OAuth onboarding redirect
#    - Guest session cleanup
#    - Refresh cookie setting
#
# 3. Complete OAuth signup route
#    - Successful signup response
#    - Refresh cookie setting
#    - Validation error propagation
#
# NOTE:
#
# - OAuth service logic is tested separately.
# - This file ONLY validates HTTP route behavior.
# - Google OAuth provider calls are mocked.
#
# =========================================================

from unittest.mock import AsyncMock, patch
from app.core.enums import UserRole
from app.services.auth.auth_tokens import (
    create_oauth_signup_token,
)

# =========================================================
# Google Login Route
# =========================================================


@patch(
    "app.api.v1.routes.auth.oauth.oauth.google.authorize_redirect",
    new_callable=AsyncMock,
)
def test_google_login_redirects_to_google(
    mock_authorize_redirect,
    client,
):

    mock_authorize_redirect.return_value = {
        "redirect": True,
    }

    response = client.get(
        "/api/v1/auth/google/login",
    )

    assert response.status_code == 200

    assert mock_authorize_redirect.called


# =========================================================
# Google Callback Route
# =========================================================


@patch(
    "app.api.v1.routes.auth.oauth.oauth.google.authorize_access_token",
    new_callable=AsyncMock,
)
def test_google_callback_missing_userinfo_redirects_error(
    mock_authorize_access_token,
    client,
):

    mock_authorize_access_token.return_value = {}

    response = client.get(
        "/api/v1/auth/google/callback",
        follow_redirects=False,
    )

    assert response.status_code == 302

    assert "/oauth/error" in response.headers["location"]


@patch(
    "app.api.v1.routes.auth.oauth.handle_google_auth_callback",
)
@patch(
    "app.api.v1.routes.auth.oauth.oauth.google.authorize_access_token",
    new_callable=AsyncMock,
)
def test_google_callback_existing_login_redirects_success(
    mock_authorize_access_token,
    mock_handle_google_auth_callback,
    client,
):

    mock_authorize_access_token.return_value = {
        "userinfo": {
            "sub": "google-id",
            "email": "oauth@example.com",
            "name": "OAuth User",
            "email_verified": True,
        }
    }

    mock_handle_google_auth_callback.return_value = {
        "type": "login",
        "refresh_token": "refresh-token",
    }

    response = client.get(
        "/api/v1/auth/google/callback",
        follow_redirects=False,
    )

    assert response.status_code == 302

    assert "/oauth/success" in response.headers["location"]

    assert "set-cookie" in response.headers


@patch(
    "app.api.v1.routes.auth.oauth.handle_google_auth_callback",
)
@patch(
    "app.api.v1.routes.auth.oauth.oauth.google.authorize_access_token",
    new_callable=AsyncMock,
)
def test_google_callback_new_oauth_redirects_onboarding(
    mock_authorize_access_token,
    mock_handle_google_auth_callback,
    client,
):

    mock_authorize_access_token.return_value = {
        "userinfo": {
            "sub": "google-id",
            "email": "oauth@example.com",
            "name": "OAuth User",
            "email_verified": True,
        }
    }

    mock_handle_google_auth_callback.return_value = {
        "type": "onboarding",
        "oauth_signup_token": "oauth-token",
    }

    response = client.get(
        "/api/v1/auth/google/callback",
        follow_redirects=False,
    )

    assert response.status_code == 302

    assert "/oauth/onboarding" in response.headers["location"]

    assert "oauth-token" in response.headers["location"]

# =========================================================
# Complete OAuth Signup Route
# =========================================================


def test_complete_google_signup_success(
    client,
):

    oauth_signup_token = create_oauth_signup_token(
        {
            "sub": "complete@example.com",
            "name": "Complete OAuth",
            "google_user_id": "google-id",
        }
    )

    response = client.post(
        "/api/v1/auth/google/complete",
        json={
            "oauth_signup_token": oauth_signup_token,
            "role": UserRole.LISTENER.value,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == ("OAuth signup completed successfully")

    assert "access_token" in data

    assert "set-cookie" in response.headers


def test_complete_google_signup_invalid_role(
    client,
):

    oauth_signup_token = create_oauth_signup_token(
        {
            "sub": "invalidrole@example.com",
            "name": "Invalid Role",
            "google_user_id": "google-id",
        }
    )

    response = client.post(
        "/api/v1/auth/google/complete",
        json={
            "oauth_signup_token": oauth_signup_token,
            "role": "admin",
        },
    )

    assert response.status_code == 403

    data = response.json()

    assert data["code"] == "INVALID_PUBLIC_ROLE"
