# =========================================================
# Password Reset OTP Flow Tests
# =========================================================
#
# This file tests:
#
# /auth/password-reset/resend
# /auth/password-reset/verify
#
# Covered areas:
#
# 1. OTP resend flow
#    - OTP regeneration
#    - Hash replacement
#    - Expiration reset
#
# 2. OTP resend protections
#    - Missing OTP rejection
#    - Verified OTP rejection
#    - Cooldown rejection
#    - Social login rejection
#    - Silent success for missing account
#
# 3. OTP verification flow
#    - Successful verification
#    - Reset token generation
#    - OTP verified state update
#
# 4. OTP verification protections
#    - Missing OTP rejection
#    - Verified OTP rejection
#    - Expired OTP rejection
#    - Maximum attempts rejection
#    - Invalid OTP rejection
#    - Attempt increment behavior
#
# NOTE:
#
# - Password reset completion is tested separately.
# - Actual email sending is mocked globally in conftest.py
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

from app.services.auth.otp_service import (
    hash_otp,
)

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
    email="resetotp@example.com",
    username="resetotp",
):

    user = User(
        name="Reset OTP",
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
    email="googleotp@example.com",
):

    user = User(
        name="Google OTP",
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


def create_password_reset_otp(
    session,
    *,
    email="resetotp@example.com",
    otp="123456",
):

    otp_record = OTP(
        email=email,
        purpose=OTPPurpose.PASSWORD_RESET.value,
        otp_hash=hash_otp(otp),
        expires_at=(get_naive_utc_now() + timedelta(minutes=5)),
        verified=False,
        attempts=0,
    )

    session.add(
        otp_record,
    )

    session.commit()

    return otp_record


def resend_password_reset_otp(
    client,
    email,
):

    return client.post(
        "/api/v1/auth/password-reset/resend",
        json={
            "email": email,
        },
    )


def verify_password_reset_otp(
    client,
    email,
    otp,
):

    return client.post(
        "/api/v1/auth/password-reset/verify",
        json={
            "email": email,
            "otp": otp,
        },
    )


# =========================================================
# OTP Resend Flow
# =========================================================


def test_password_reset_resend_success(
    client,
    session,
):

    email = "resend@example.com"

    create_local_user(
        session,
        email=email,
        username="resenduser",
    )

    otp_record = create_password_reset_otp(
        session,
        email=email,
    )

    otp_record.created_at = get_naive_utc_now() - timedelta(minutes=2)

    old_hash = otp_record.otp_hash

    session.add(
        otp_record,
    )

    session.commit()

    response = resend_password_reset_otp(
        client,
        email,
    )

    assert response.status_code == 200

    updated_otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    assert updated_otp.otp_hash != old_hash

    assert updated_otp.verified is False


# =========================================================
# OTP Resend Protections
# =========================================================


def test_password_reset_resend_missing_account_silent_success(
    client,
):

    response = resend_password_reset_otp(
        client,
        "missing@example.com",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "OTP resent successfully"


def test_password_reset_resend_google_only_account(
    client,
    session,
):

    create_google_only_user(
        session,
        email="googleonly@example.com",
    )

    response = resend_password_reset_otp(
        client,
        "googleonly@example.com",
    )

    assert response.status_code == 403

    data = response.json()

    assert data["code"] == "SOCIAL_LOGIN_PASSWORD_RESET_UNAVAILABLE"


def test_password_reset_resend_missing_otp(
    client,
    session,
):

    email = "missingotp@example.com"

    create_local_user(
        session,
        email=email,
        username="missingotp",
    )

    response = resend_password_reset_otp(
        client,
        email,
    )

    assert response.status_code == 404

    data = response.json()

    assert data["code"] == "OTP_NOT_FOUND"


def test_password_reset_resend_verified_otp(
    client,
    session,
):

    email = "verifiedotp@example.com"

    create_local_user(
        session,
        email=email,
        username="verifiedotp",
    )

    otp_record = create_password_reset_otp(
        session,
        email=email,
    )

    otp_record.verified = True

    otp_record.created_at = get_naive_utc_now() - timedelta(minutes=2)

    session.add(
        otp_record,
    )

    session.commit()

    response = resend_password_reset_otp(
        client,
        email,
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "OTP_ALREADY_VERIFIED"


def test_password_reset_resend_cooldown(
    client,
    session,
):

    email = "cooldownotp@example.com"

    create_local_user(
        session,
        email=email,
        username="cooldownotp",
    )

    create_password_reset_otp(
        session,
        email=email,
    )

    response = resend_password_reset_otp(
        client,
        email,
    )

    assert response.status_code == 429

    data = response.json()

    assert data["code"] == "OTP_RESEND_COOLDOWN_ACTIVE"


# =========================================================
# OTP Verification Flow
# =========================================================


def test_password_reset_verify_success(
    client,
    session,
):

    email = "verify@example.com"

    create_local_user(
        session,
        email=email,
        username="verifyuser",
    )

    create_password_reset_otp(
        session,
        email=email,
        otp="123456",
    )

    response = verify_password_reset_otp(
        client,
        email,
        "123456",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "otp_verified"

    assert data["reset_token"] is not None

    otp_record = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    assert otp_record.verified is True


# =========================================================
# OTP Verification Protections
# =========================================================


def test_password_reset_verify_missing_otp(
    client,
):

    response = verify_password_reset_otp(
        client,
        "missing@example.com",
        "123456",
    )

    assert response.status_code == 404

    data = response.json()

    assert data["code"] == "OTP_NOT_FOUND"


def test_password_reset_verify_already_verified(
    client,
    session,
):

    email = "alreadyverified@example.com"

    create_local_user(
        session,
        email=email,
        username="alreadyverified",
    )

    otp_record = create_password_reset_otp(
        session,
        email=email,
    )

    otp_record.verified = True

    session.add(
        otp_record,
    )

    session.commit()

    response = verify_password_reset_otp(
        client,
        email,
        "123456",
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "OTP_ALREADY_VERIFIED"


def test_password_reset_verify_expired_otp(
    client,
    session,
):

    email = "expiredverify@example.com"

    create_local_user(
        session,
        email=email,
        username="expiredverify",
    )

    otp_record = create_password_reset_otp(
        session,
        email=email,
    )

    otp_record.expires_at = get_naive_utc_now() - timedelta(minutes=10)

    session.add(
        otp_record,
    )

    session.commit()

    response = verify_password_reset_otp(
        client,
        email,
        "123456",
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "OTP_EXPIRED"


def test_password_reset_verify_max_attempts(
    client,
    session,
):

    email = "maxattempts@example.com"

    create_local_user(
        session,
        email=email,
        username="maxattempts",
    )

    otp_record = create_password_reset_otp(
        session,
        email=email,
    )

    otp_record.attempts = 5

    session.add(
        otp_record,
    )

    session.commit()

    response = verify_password_reset_otp(
        client,
        email,
        "123456",
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "OTP_MAX_ATTEMPTS_EXCEEDED"


def test_password_reset_verify_invalid_otp(
    client,
    session,
):

    email = "invalidotp@example.com"

    create_local_user(
        session,
        email=email,
        username="invalidotp",
    )

    create_password_reset_otp(
        session,
        email=email,
        otp="123456",
    )

    response = verify_password_reset_otp(
        client,
        email,
        "000000",
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "INVALID_OTP"

    updated_otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    assert updated_otp.attempts == 1
