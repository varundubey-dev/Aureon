# =========================================================
# Auth Token Tests
# =========================================================
#
# This file tests:
#
# auth_tokens.py
#
# Covered areas:
#
# 1. Access tokens
#    - Creation
#    - Verification
#    - Invalid token rejection
#    - Wrong token type rejection
#
# 2. Refresh tokens
#    - Creation
#    - Verification
#    - Session ID preservation
#    - Wrong token type rejection
#
# 3. Signup tokens
#    - Creation
#    - Verification
#    - Missing subject rejection
#    - Wrong token type rejection
#
# 4. Password reset tokens
#    - Creation
#    - Verification
#    - Wrong token type rejection
#
# 5. OAuth signup tokens
#    - Creation
#    - Verification
#    - Payload preservation
#    - Wrong token type rejection
#
# NOTE:
#
# - JWT cryptography internals are handled by jose.
# - This file tests ONLY application token behavior.
#
# =========================================================

from jose import jwt

from app.core.config import settings

from app.services.auth.auth_tokens import (
    create_access_token,
    verify_access_token,
    create_refresh_token,
    verify_refresh_token,
    create_signup_token,
    verify_signup_token,
    create_password_reset_token,
    verify_password_reset_token,
    create_oauth_signup_token,
    verify_oauth_signup_token,
)

# =========================================================
# Access Tokens
# =========================================================


def test_create_and_verify_access_token():

    token = create_access_token(
        {
            "sub": "user-id",
            "token_version": 0,
        }
    )

    payload = verify_access_token(
        token,
    )

    assert payload is not None

    assert payload["sub"] == "user-id"

    assert payload["token_version"] == 0

    assert payload["type"] == "access"


def test_verify_access_token_invalid_token():

    payload = verify_access_token(
        "invalid-token",
    )

    assert payload is None


def test_verify_access_token_wrong_type():

    token = create_signup_token(
        "wrongtype@example.com",
    )

    payload = verify_access_token(
        token,
    )

    assert payload is None


# =========================================================
# Refresh Tokens
# =========================================================


def test_create_and_verify_refresh_token():

    token, expiration = create_refresh_token(
        "user-id",
        "session-id",
    )

    payload = verify_refresh_token(
        token,
    )

    assert payload is not None

    assert payload["sub"] == "user-id"

    assert payload["jti"] == "session-id"

    assert payload["type"] == "refresh"

    assert expiration is not None


def test_verify_refresh_token_invalid_token():

    payload = verify_refresh_token(
        "invalid-token",
    )

    assert payload is None


def test_verify_refresh_token_wrong_type():

    token = create_access_token(
        {
            "sub": "user-id",
        }
    )

    payload = verify_refresh_token(
        token,
    )

    assert payload is None


# =========================================================
# Signup Tokens
# =========================================================


def test_create_and_verify_signup_token():

    token = create_signup_token(
        "signup@example.com",
    )

    email = verify_signup_token(
        token,
    )

    assert email == "signup@example.com"


def test_verify_signup_token_invalid_token():

    email = verify_signup_token(
        "invalid-token",
    )

    assert email is None


def test_verify_signup_token_wrong_type():

    token = create_access_token(
        {
            "sub": "signup@example.com",
        }
    )

    email = verify_signup_token(
        token,
    )

    assert email is None


def test_verify_signup_token_missing_subject():

    token = jwt.encode(
        {
            "type": "signup",
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    email = verify_signup_token(
        token,
    )

    assert email is None


# =========================================================
# Password Reset Tokens
# =========================================================


def test_create_and_verify_password_reset_token():

    token = create_password_reset_token(
        "reset@example.com",
    )

    email = verify_password_reset_token(
        token,
    )

    assert email == "reset@example.com"


def test_verify_password_reset_token_invalid_token():

    email = verify_password_reset_token(
        "invalid-token",
    )

    assert email is None


def test_verify_password_reset_token_wrong_type():

    token = create_signup_token(
        "reset@example.com",
    )

    email = verify_password_reset_token(
        token,
    )

    assert email is None


# =========================================================
# OAuth Signup Tokens
# =========================================================


def test_create_and_verify_oauth_signup_token():

    token = create_oauth_signup_token(
        {
            "sub": "oauth@example.com",
            "name": "OAuth User",
            "google_user_id": "google-id",
        }
    )

    payload = verify_oauth_signup_token(
        token,
    )

    assert payload is not None

    assert payload["sub"] == "oauth@example.com"

    assert payload["name"] == "OAuth User"

    assert payload["google_user_id"] == "google-id"

    assert payload["type"] == "oauth_signup"


def test_verify_oauth_signup_token_invalid_token():

    payload = verify_oauth_signup_token(
        "invalid-token",
    )

    assert payload is None


def test_verify_oauth_signup_token_wrong_type():

    token = create_access_token(
        {
            "sub": "oauth@example.com",
        }
    )

    payload = verify_oauth_signup_token(
        token,
    )

    assert payload is None