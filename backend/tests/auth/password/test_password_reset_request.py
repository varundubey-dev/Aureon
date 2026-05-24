# =========================================================
# Password Reset Request Flow Tests
# =========================================================
#
# This file tests:
#
# /auth/password-reset/request
#
# Covered areas:
#
# 1. Successful password reset request
#    - OTP creation
#    - PASSWORD_RESET purpose assignment
#    - Email normalization
#    - Email payload generation
#
# 2. Silent security protections
#    - Missing account silent success
#
# 3. Social login protections
#    - OAuth-only account rejection
#
# 4. OTP resend protections
#    - Cooldown enforcement
#    - Existing OTP reset behavior
#    - Expired OTP replacement behavior
#
# NOTE:
#
# - OTP verification is tested separately.
# - Password reset completion is tested separately.
# - Actual email sending is NOT tested here.
#
# =========================================================

from datetime import timedelta

from sqlmodel import select

from app.core.enums import (
    AuthProviderType,
    OTPPurpose,
    UserRole,
)

from app.models.auth.auth_provider import AuthProvider
from app.models.auth.otp import OTP
from app.models.auth.user import User

from app.services.auth.password_service import (
    hash_password,
)

from app.utils.datetime import (
    get_naive_utc_now,
)

# =========================================================
# Helpers
# =========================================================


def create_local_user(
    session,
    *,
    email="reset@example.com",
    username="resetuser",
):

    user = User(
        name="Reset User",
        username=username,
        username_normalized=username,
        email=email,
        password_hash=hash_password(
            "StrongPassword123!",
        ),
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
    )

    session.add(user)
    session.flush()

    provider = AuthProvider(
        user_id=user.id,
        provider=AuthProviderType.LOCAL.value,
        provider_user_id=email,
    )

    session.add(provider)

    session.commit()

    return user


def create_google_only_user(
    session,
    *,
    email="google@example.com",
):

    user = User(
        name="Google User",
        username=None,
        username_normalized=None,
        email=email,
        password_hash=None,
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
    )

    session.add(user)
    session.flush()

    provider = AuthProvider(
        user_id=user.id,
        provider=AuthProviderType.GOOGLE.value,
        provider_user_id="google-user-id",
    )

    session.add(provider)

    session.commit()

    return user


def request_password_reset(
    client,
    email,
):

    return client.post(
        "/api/v1/auth/password-reset/request",
        json={
            "email": email,
        },
    )


# =========================================================
# Successful Request Flow
# =========================================================


def test_password_reset_request_success(
    client,
    session,
):

    email = "resetsuccess@example.com"

    create_local_user(
        session,
        email=email,
        username="resetsuccess",
    )

    response = request_password_reset(
        client,
        email,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "otp_sent"

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
            OTP.purpose == OTPPurpose.PASSWORD_RESET.value,
        )
    ).first()

    assert otp is not None

    assert otp.verified is False


def test_password_reset_request_normalizes_email(
    client,
    session,
):

    create_local_user(
        session,
        email="normalize@example.com",
        username="normalize",
    )

    response = request_password_reset(
        client,
        "NORMALIZE@EXAMPLE.COM",
    )

    assert response.status_code == 200

    otp = session.exec(
        select(OTP).where(
            OTP.email == "normalize@example.com",
        )
    ).first()

    assert otp is not None


# =========================================================
# Silent Security Protections
# =========================================================


def test_password_reset_request_missing_account_silent_success(
    client,
    session,
):

    response = request_password_reset(
        client,
        "missing@example.com",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "otp_sent"

    otp = session.exec(
        select(OTP).where(
            OTP.email == "missing@example.com",
        )
    ).first()

    assert otp is None


# =========================================================
# Social Login Protections
# =========================================================


def test_password_reset_request_google_only_account(
    client,
    session,
):

    create_google_only_user(
        session,
        email="googleonly@example.com",
    )

    response = request_password_reset(
        client,
        "googleonly@example.com",
    )

    assert response.status_code == 403

    data = response.json()

    assert data["code"] == "SOCIAL_LOGIN_PASSWORD_RESET_UNAVAILABLE"


# =========================================================
# OTP Cooldown Protections
# =========================================================


def test_password_reset_request_resend_cooldown(
    client,
    session,
):

    email = "cooldownreset@example.com"

    create_local_user(
        session,
        email=email,
        username="cooldownreset",
    )

    first_response = request_password_reset(
        client,
        email,
    )

    assert first_response.status_code == 200

    second_response = request_password_reset(
        client,
        email,
    )

    assert second_response.status_code == 429

    data = second_response.json()

    assert data["code"] == "OTP_RESEND_COOLDOWN_ACTIVE"


def test_password_reset_request_replaces_expired_otp(
    client,
    session,
):

    email = "expiredreset@example.com"

    create_local_user(
        session,
        email=email,
        username="expiredreset",
    )

    first_response = request_password_reset(
        client,
        email,
    )

    assert first_response.status_code == 200

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
            OTP.purpose == OTPPurpose.PASSWORD_RESET.value,
        )
    ).first()

    old_hash = otp.otp_hash

    # SQLite timezone handling issue in tests
    otp.expires_at = get_naive_utc_now() - timedelta(minutes=10)

    session.add(
        otp,
    )

    session.commit()

    second_response = request_password_reset(
        client,
        email,
    )

    assert second_response.status_code == 200

    updated_otp = session.exec(
        select(OTP).where(
            OTP.email == email,
            OTP.purpose == OTPPurpose.PASSWORD_RESET.value,
        )
    ).first()

    assert updated_otp.otp_hash != old_hash

    assert updated_otp.verified is False
