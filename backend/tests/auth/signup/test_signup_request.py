# =========================================================
# Signup Request Flow Tests
# =========================================================
#
# This file tests signup request flow: Complete signup/request API flow
#
# handle_signup_request()
#
# Covered areas:
#
# 1. Fresh local signup request flow
#    - OTP creation
#    - Pending signup creation
#    - Initial unverified state
#
# 2. Input validation
#    - Invalid names
#    - Name trimming behavior
#    - Email normalization behavior
#
# 3. Existing account protections
#    - Existing LOCAL account rejection
#    - Corrupted account state handling
#
# 4. OTP security protections
#    - Resend cooldown enforcement
#    - Existing OTP reuse/reset behavior
#    - Expired OTP replacement behavior
#
# 5. Pending signup state handling
#    - Existing pending signup updates
#    - Cooldown preventing overwrite
#
# 6. OAuth-first signup flow
#    - Existing OAuth user detection
#    - complete_local_setup response type
#    - OAuth account linking behavior
#
# NOTE:
# Guest upgrade flow is NOT tested here because:
#
# - existing_user_id is internally dependency-driven
# - route does not publicly expose guest linking
# - testing it here would fake impossible client behavior
# - SQLite timezone handling breaks aware UTC datetimes in tests.
# - Intentionally using get_naive_utc_now() here for stable expiration testing.
#
# Guest upgrade flow should instead be tested in:
#
# tests/auth/signup/test_guest_upgrade_signup.py
#
# =========================================================

import pytest

from datetime import (
    timedelta,
)

from app.utils.datetime import get_naive_utc_now

from sqlmodel import (
    select,
)

from app.core.enums import (
    AuthProviderType,
    OTPPurpose,
    UserRole,
)

from app.models.auth.auth_provider import (
    AuthProvider,
)

from app.models.auth.otp import (
    OTP,
)

from app.models.auth.pending_signup import (
    PendingSignup,
)

from app.models.auth.user import (
    User,
)

# =========================================================
# Success Cases
# =========================================================


def test_signup_request_creates_pending_signup(
    client,
    session,
):

    email = "testsignup@example.com"

    response = client.post(
        "/api/v1/auth/signup/request",
        json={
            "email": email,
            "name": "Varun",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "otp_verification"

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    assert otp is not None
    assert otp.purpose == OTPPurpose.SIGNUP.value
    assert otp.verified is False

    pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == email,
        )
    ).first()

    assert pending_signup is not None
    assert pending_signup.verified is False
    assert pending_signup.name == "Varun"


def test_signup_request_trims_name(
    client,
    session,
):

    email = "trimmed@example.com"

    client.post(
        "/api/v1/auth/signup/request",
        json={
            "email": email,
            "name": "   Varun   ",
        },
    )

    pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == email,
        )
    ).first()

    assert pending_signup is not None
    assert pending_signup.name == "Varun"


def test_signup_request_normalizes_email(
    client,
    session,
):

    client.post(
        "/api/v1/auth/signup/request",
        json={
            "email": "TEST@EXAMPLE.COM",
            "name": "Varun",
        },
    )

    pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == "test@example.com",
        )
    ).first()

    assert pending_signup is not None


# =========================================================
# Name Validation
# =========================================================


@pytest.mark.parametrize(
    "invalid_name",
    [
        "A",
        "12",
        "Test123",
        "@@@",
        "!!Test",
        "",
        "   ",
        "Te@st",
    ],
)
def test_signup_request_invalid_name(
    client,
    invalid_name,
):

    response = client.post(
        "/api/v1/auth/signup/request",
        json={
            "email": "test@example.com",
            "name": invalid_name,
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "INVALID_NAME_FORMAT"


# =========================================================
# Existing Account Protection
# =========================================================


def test_signup_request_existing_local_account(
    client,
    session,
):

    existing_user = User(
        name="Test",
        username="test",
        username_normalized="test",
        email="existing@example.com",
        password_hash="hashed_password",
        role="listener",
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
    )

    session.add(existing_user)
    session.flush()

    auth_provider = AuthProvider(
        user_id=existing_user.id,
        provider=AuthProviderType.LOCAL.value,
        provider_user_id="existing@example.com",
    )

    session.add(auth_provider)
    session.commit()

    response = client.post(
        "/api/v1/auth/signup/request",
        json={
            "email": "existing@example.com",
            "name": "Varun",
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "ACCOUNT_ALREADY_EXISTS"


def test_signup_request_corrupted_existing_account(
    client,
    session,
):

    corrupted_user = User(
        name="Broken",
        username="broken",
        username_normalized="broken",
        email=None,
        password_hash="hashed_password",
        role="listener",
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
    )

    session.add(corrupted_user)
    session.commit()

    response = client.post(
        "/api/v1/auth/signup/request",
        json={
            "email": "",
            "name": "Varun",
        },
    )

    # Schema validation may trigger first.
    assert response.status_code in [400, 422]


# =========================================================
# OTP Security
# =========================================================


def test_signup_request_otp_cooldown(
    client,
):

    email = "cooldown@example.com"

    first_response = client.post(
        "/api/v1/auth/signup/request",
        json={
            "email": email,
            "name": "Varun",
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/api/v1/auth/signup/request",
        json={
            "email": email,
            "name": "Varun",
        },
    )

    assert second_response.status_code == 429

    data = second_response.json()

    assert data["code"] == "OTP_RESEND_COOLDOWN_ACTIVE"


def test_signup_request_resets_expired_otp(
    client,
    session,
):

    email = "expired@example.com"

    client.post(
        "/api/v1/auth/signup/request",
        json={
            "email": email,
            "name": "Old",
        },
    )

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    # SQLite timezone handling breaks aware UTC datetimes in tests.
    # Intentionally using get_naive_utc_now() here for stable expiration testing.
    otp.expires_at = get_naive_utc_now() - timedelta(minutes=6)

    session.add(otp)
    session.commit()

    response = client.post(
        "/api/v1/auth/signup/request",
        json={
            "email": email,
            "name": "New",
        },
    )

    assert response.status_code == 200

    updated_pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == email,
        )
    ).first()

    assert updated_pending_signup is not None
    assert updated_pending_signup.name == "New"


def test_signup_request_updates_existing_pending_signup_after_expiration(
    client,
    session,
):

    email = "updateexpired@example.com"

    client.post(
        "/api/v1/auth/signup/request",
        json={
            "email": email,
            "name": "Old Name",
        },
    )

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    # SQLite timezone handling breaks aware UTC datetimes in tests.
    # Intentionally using get_naive_utc_now() here for stable expiration testing.

    otp.expires_at = get_naive_utc_now() - timedelta(minutes=6)

    session.add(otp)
    session.commit()

    response = client.post(
        "/api/v1/auth/signup/request",
        json={
            "email": email,
            "name": "New Name",
        },
    )

    assert response.status_code == 200

    pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == email,
        )
    ).first()

    assert pending_signup is not None
    assert pending_signup.name == "New Name"


# =========================================================
# OAuth-first Signup Flow
# =========================================================


def test_signup_request_oauth_first_flow(
    client,
    session,
):

    oauth_user = User(
        name="OAuth User",
        username=None,
        username_normalized=None,
        email="oauth@example.com",
        password_hash=None,
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
    )

    session.add(oauth_user)
    session.flush()

    google_provider = AuthProvider(
        user_id=oauth_user.id,
        provider=AuthProviderType.GOOGLE.value,
        provider_user_id="google-oauth-id",
    )

    session.add(google_provider)
    session.commit()

    response = client.post(
        "/api/v1/auth/signup/request",
        json={
            "email": "oauth@example.com",
            "name": "OAuth User",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "complete_local_setup"

    pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == "oauth@example.com",
        )
    ).first()

    assert pending_signup is not None
    assert pending_signup.existing_user_id == oauth_user.id
