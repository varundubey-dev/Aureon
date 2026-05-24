# =========================================================
# Signup OTP Flow Tests
# =========================================================
#
# This file tests: Complete signup/verify and signup/resend API flow
#
# 1. Signup OTP verification flow
#    - Successful OTP verification
#    - Signup token generation
#    - Username suggestion generation
#    - Verified state updates
#
# 2. OTP validation protections
#    - Missing OTP handling
#    - Invalid OTP rejection
#    - Expired OTP rejection
#    - Already verified OTP rejection
#    - Maximum OTP attempt enforcement
#
# 3. Pending signup integrity checks
#    - Missing pending signup detection
#    - Already verified signup rejection
#    - Corrupted signup state handling
#
# 4. OTP attempt tracking
#    - Failed attempt incrementing
#    - Attempt persistence
#    - Max-attempt lockout behavior
#
# 5. OAuth-first verification flow
#    - Existing OAuth account detection
#    - complete_local_setup response type
#
# 6. Signup resend OTP flow
#    - Successful OTP resend
#    - OTP regeneration
#    - Cooldown enforcement
#    - Verified-state protections
#    - Missing-state protections
#
# NOTE:
#
# - SQLite timezone handling breaks aware UTC datetimes in tests.
# - Intentionally using get_naive_utc_now() here for stable expiration testing.
#
# =========================================================

from datetime import timedelta

from sqlmodel import select

from app.core.config import settings
from app.core.enums import (
    AuthProviderType,
    UserRole,
)

from app.models.auth.auth_provider import AuthProvider
from app.models.auth.otp import OTP
from app.models.auth.pending_signup import PendingSignup
from app.models.auth.user import User

from app.services.auth.otp_service import hash_otp

from app.utils.datetime import get_utc_now, get_naive_utc_now


# =========================================================
# Helpers
# =========================================================


def create_signup_state(
    client,
    email="test@example.com",
    name="Varun",
):

    response = client.post(
        "/api/v1/auth/signup/request",
        json={
            "email": email,
            "name": name,
        },
    )

    assert response.status_code == 200


# =========================================================
# Success Flow
# =========================================================


def test_verify_signup_otp_success(
    client,
    session,
):

    email = "verify@example.com"

    create_signup_state(
        client,
        email=email,
    )

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()
    
    raw_otp = "123456"

    otp.otp_hash = hash_otp(
        raw_otp,
    )

    session.add(otp)
    session.commit()

    response = client.post(
        "/api/v1/auth/signup/verify",
        json={
            "email": email,
            "otp": raw_otp,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "normal_signup"

    assert "signup_token" in data

    assert isinstance(
        data["username_suggestions"],
        list,
    )

    updated_otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == email,
        )
    ).first()

    assert updated_otp.verified is True
    assert pending_signup.verified is True


def test_verify_signup_otp_oauth_first_flow(
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

    provider = AuthProvider(
        user_id=oauth_user.id,
        provider=AuthProviderType.GOOGLE.value,
        provider_user_id="google-id",
    )

    session.add(provider)
    session.commit()

    create_signup_state(
        client,
        email="oauth@example.com",
    )

    otp = session.exec(
        select(OTP).where(
            OTP.email == "oauth@example.com",
        )
    ).first()

    raw_otp = "123456"

    otp.otp_hash = hash_otp(
        raw_otp,
    )

    session.add(otp)
    session.commit()

    response = client.post(
        "/api/v1/auth/signup/verify",
        json={
            "email": "oauth@example.com",
            "otp": raw_otp,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "complete_local_setup"


# =========================================================
# OTP Validation Protections
# =========================================================


def test_verify_signup_otp_not_found(
    client,
):

    response = client.post(
        "/api/v1/auth/signup/verify",
        json={
            "email": "missing@example.com",
            "otp": "123456",
        },
    )

    assert response.status_code == 404

    data = response.json()

    assert data["code"] == "OTP_NOT_FOUND"


def test_verify_signup_otp_pending_signup_corrupted(
    client,
    session,
):

    email = "corrupted@example.com"

    create_signup_state(
        client,
        email=email,
    )

    pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == email,
        )
    ).first()

    session.delete(
        pending_signup,
    )

    session.commit()

    response = client.post(
        "/api/v1/auth/signup/verify",
        json={
            "email": email,
            "otp": "123456",
        },
    )

    assert response.status_code == 500

    data = response.json()

    assert data["code"] == "PENDING_SIGNUP_CORRUPTED"


def test_verify_signup_otp_signup_already_verified(
    client,
    session,
):

    email = "verifiedsignup@example.com"

    create_signup_state(
        client,
        email=email,
    )

    pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == email,
        )
    ).first()

    pending_signup.verified = True

    session.add(pending_signup)
    session.commit()

    response = client.post(
        "/api/v1/auth/signup/verify",
        json={
            "email": email,
            "otp": "123456",
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "SIGNUP_ALREADY_VERIFIED"


def test_verify_signup_otp_already_verified(
    client,
    session,
):

    email = "verifiedotp@example.com"

    create_signup_state(
        client,
        email=email,
    )

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    otp.verified = True

    session.add(otp)
    session.commit()

    response = client.post(
        "/api/v1/auth/signup/verify",
        json={
            "email": email,
            "otp": "123456",
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "OTP_ALREADY_VERIFIED"


def test_verify_signup_otp_expired(
    client,
    session,
):

    email = "expired@example.com"

    create_signup_state(
        client,
        email=email,
    )

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()
    
     # - SQLite timezone handling breaks aware UTC datetimes in tests.
     # - Intentionally using get_naive_utc_now() here for stable expiration testing.

    otp.expires_at = (
          get_naive_utc_now() - timedelta(minutes=10)
     )

    session.add(otp)
    session.commit()

    response = client.post(
        "/api/v1/auth/signup/verify",
        json={
            "email": email,
            "otp": "123456",
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "OTP_EXPIRED"


def test_verify_signup_otp_invalid_otp_increments_attempts(
    client,
    session,
):

    email = "attempts@example.com"

    create_signup_state(
        client,
        email=email,
    )

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    initial_attempts = otp.attempts

    response = client.post(
        "/api/v1/auth/signup/verify",
        json={
            "email": email,
            "otp": "wrongotp",
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "INVALID_OTP"

    updated_otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    assert updated_otp.attempts == (
        initial_attempts + 1
    )


def test_verify_signup_otp_max_attempts_exceeded(
    client,
    session,
):

    email = "maxattempts@example.com"

    create_signup_state(
        client,
        email=email,
    )

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    otp.attempts = (
        settings.OTP_MAX_ATTEMPTS
    )

    session.add(otp)
    session.commit()

    response = client.post(
        "/api/v1/auth/signup/verify",
        json={
            "email": email,
            "otp": "123456",
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert (
        data["code"]
        == "OTP_MAX_ATTEMPTS_EXCEEDED"
    )


# =========================================================
# Resend OTP Flow
# =========================================================


def test_resend_signup_otp_success(
    client,
    session,
):

    email = "resend@example.com"

    create_signup_state(
        client,
        email=email,
    )

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    old_hash = otp.otp_hash
    
    
     # - SQLite timezone handling breaks aware UTC datetimes in tests.
     # - Intentionally using get_naive_utc_now() here for stable expiration testing.
    otp.created_at = (
          get_naive_utc_now()
          - timedelta(
               seconds=(
                    settings.OTP_RESEND_COOLDOWN_SECONDS
                    + 5
               )
          )
          )

    otp.attempts = 3

    session.add(otp)
    session.commit()

    response = client.post(
        "/api/v1/auth/signup/resend",
        json={
            "email": email,
        },
    )

    assert response.status_code == 200

    updated_otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    assert updated_otp.otp_hash != old_hash
    assert updated_otp.attempts == 0
    assert updated_otp.verified is False


def test_resend_signup_otp_cooldown_active(
    client,
):

    email = "cooldown@example.com"

    create_signup_state(
        client,
        email=email,
    )

    response = client.post(
        "/api/v1/auth/signup/resend",
        json={
            "email": email,
        },
    )

    assert response.status_code == 429

    data = response.json()

    assert (
        data["code"]
        == "OTP_RESEND_COOLDOWN_ACTIVE"
    )


def test_resend_signup_otp_not_found(
    client,
):

    response = client.post(
        "/api/v1/auth/signup/resend",
        json={
            "email": "missing@example.com",
        },
    )

    assert response.status_code == 404

    data = response.json()

    assert data["code"] == "OTP_NOT_FOUND"


def test_resend_signup_pending_signup_missing(
    client,
    session,
):

    email = "missingpending@example.com"

    create_signup_state(
        client,
        email=email,
    )

    pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == email,
        )
    ).first()

    session.delete(
        pending_signup,
    )

    session.commit()

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    otp.created_at = (
        get_utc_now()
        - timedelta(
            seconds=(
                settings.OTP_RESEND_COOLDOWN_SECONDS
                + 5
            )
        )
    )

    session.add(otp)
    session.commit()

    response = client.post(
        "/api/v1/auth/signup/resend",
        json={
            "email": email,
        },
    )

    assert response.status_code == 404

    data = response.json()

    assert (
        data["code"]
        == "PENDING_SIGNUP_NOT_FOUND"
    )


def test_resend_signup_already_verified_signup(
    client,
    session,
):

    email = "verifiedsignup@example.com"

    create_signup_state(
        client,
        email=email,
    )

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == email,
        )
    ).first()

    otp.created_at = (
        get_utc_now()
        - timedelta(
            seconds=(
                settings.OTP_RESEND_COOLDOWN_SECONDS
                + 5
            )
        )
    )

    pending_signup.verified = True

    session.add(otp)
    session.add(pending_signup)
    session.commit()

    response = client.post(
        "/api/v1/auth/signup/resend",
        json={
            "email": email,
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert (
        data["code"]
        == "SIGNUP_ALREADY_VERIFIED"
    )


def test_resend_signup_already_verified_otp(
    client,
    session,
):

    email = "verifiedotp@example.com"

    create_signup_state(
        client,
        email=email,
    )

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    otp.created_at = (
        get_utc_now()
        - timedelta(
            seconds=(
                settings.OTP_RESEND_COOLDOWN_SECONDS
                + 5
            )
        )
    )

    otp.verified = True

    session.add(otp)
    session.commit()

    response = client.post(
        "/api/v1/auth/signup/resend",
        json={
            "email": email,
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "OTP_ALREADY_VERIFIED"