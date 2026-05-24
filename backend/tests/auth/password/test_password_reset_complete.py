# =========================================================
# Password Reset Completion Flow Tests
# =========================================================
#
# This file tests:
#
# /auth/password-reset/complete
#
# Covered areas:
#
# 1. Successful password reset
#    - Password replacement
#    - Token version invalidation
#    - Refresh session cleanup
#    - OTP cleanup
#    - Refresh cookie clearing
#
# 2. Reset token protections
#    - Invalid token rejection
#    - Missing user rejection
#
# 3. Provider protections
#    - Social login reset rejection
#
# 4. Password validation protections
#    - Password mismatch rejection
#    - Weak password rejection
#
# NOTE:
#
# - OTP verification flow is tested separately.
# - This file assumes OTP verification already succeeded.
#
# =========================================================

from sqlmodel import select

from app.core.enums import (
    AuthProviderType,
    OTPPurpose,
    UserRole,
)

from app.models.auth.auth_provider import AuthProvider
from app.models.auth.otp import OTP
from app.models.auth.refresh_session import RefreshSession
from app.models.auth.user import User

from app.services.auth.auth_sessions import (
    create_user_auth_session,
)

from app.services.auth.auth_tokens import (
    create_password_reset_token,
)

from app.services.auth.otp_service import (
    hash_otp,
)

from app.services.auth.password_service import (
    hash_password,
    verify_password,
)

from app.utils.datetime import (
    get_utc_now,
)

from datetime import timedelta

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
            "OldPassword123!",
        ),
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
        token_version=0,
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
    email="googleonly@example.com",
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
        token_version=0,
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
    email,
):

    otp_record = OTP(
        email=email,
        purpose=OTPPurpose.PASSWORD_RESET.value,
        otp_hash=hash_otp("123456"),
        expires_at=get_utc_now() + timedelta(minutes=5),
        verified=True,
    )

    session.add(otp_record)
    session.commit()

    return otp_record


def complete_password_reset(
    client,
    *,
    reset_token,
    new_password="NewStrongPassword123!",
    confirm_password="NewStrongPassword123!",
):

    return client.post(
        "/api/v1/auth/password-reset/complete",
        json={
            "reset_token": reset_token,
            "new_password": new_password,
            "confirm_password": confirm_password,
        },
    )


# =========================================================
# Successful Password Reset
# =========================================================


def test_complete_password_reset_success(
    client,
    session,
):

    user = create_local_user(
        session,
    )

    create_password_reset_otp(
        session,
        email=user.email,
    )

    (
        access_token,
        refresh_token,
    ) = create_user_auth_session(
        session,
        user,
    )

    session.commit()

    old_password_hash = user.password_hash

    assert user.email is not None

    reset_token = create_password_reset_token(
        user.email,
    )

    response = complete_password_reset(
        client,
        reset_token=reset_token,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "password_reset_completed"

    updated_user = session.get(
        User,
        user.id,
    )

    assert updated_user.token_version == 1

    assert updated_user.password_hash != old_password_hash

    assert verify_password(
        "NewStrongPassword123!",
        updated_user.password_hash,
    )

    refresh_sessions = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
        )
    ).all()

    assert len(refresh_sessions) == 0

    otp_record = session.exec(
        select(OTP).where(
            OTP.email == user.email,
            OTP.purpose == OTPPurpose.PASSWORD_RESET.value,
        )
    ).first()

    assert otp_record is None

    set_cookie_header = response.headers.get(
        "set-cookie",
        "",
    ).lower()

    assert "refresh_token=" in set_cookie_header

    assert "max-age=0" in set_cookie_header


# =========================================================
# Reset Token Protections
# =========================================================


def test_complete_password_reset_invalid_token(
    client,
):

    response = complete_password_reset(
        client,
        reset_token="invalid-token",
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "INVALID_RESET_TOKEN"


def test_complete_password_reset_user_not_found(
    client,
):

    reset_token = create_password_reset_token(
        "missing@example.com",
    )

    response = complete_password_reset(
        client,
        reset_token=reset_token,
    )

    assert response.status_code == 404

    data = response.json()

    assert data["code"] == "USER_NOT_FOUND"


# =========================================================
# Social Login Protections
# =========================================================


def test_complete_password_reset_social_login_account(
    client,
    session,
):

    user = create_google_only_user(
        session,
    )
    
    assert user.email is not None

    reset_token = create_password_reset_token(
        user.email,
    )

    response = complete_password_reset(
        client,
        reset_token=reset_token,
    )

    assert response.status_code == 403

    data = response.json()

    assert data["code"] == "SOCIAL_LOGIN_PASSWORD_RESET_UNAVAILABLE"


# =========================================================
# Password Validation
# =========================================================


def test_complete_password_reset_password_mismatch(
    client,
    session,
):

    user = create_local_user(
        session,
    )
    
    assert user.email is not None

    reset_token = create_password_reset_token(
        user.email,
    )

    response = complete_password_reset(
        client,
        reset_token=reset_token,
        new_password="StrongPassword123!",
        confirm_password="DifferentPassword123!",
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "PASSWORDS_DO_NOT_MATCH"


def test_complete_password_reset_weak_password(
    client,
    session,
):

    user = create_local_user(
        session,
    )
    
    assert user.email is not None

    reset_token = create_password_reset_token(
        user.email,
    )

    response = complete_password_reset(
        client,
        reset_token=reset_token,
        new_password="123",
        confirm_password="123",
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "WEAK_PASSWORD"
