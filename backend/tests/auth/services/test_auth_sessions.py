# =========================================================
# Auth Session Tests
# =========================================================
#
# This file tests:
#
# auth_sessions.py
#
# Covered areas:
#
# 1. Refresh session creation
#    - UUID generation
#    - Token hashing
#    - Expiration assignment
#
# 2. User auth session creation
#    - Access token creation
#    - Refresh session persistence
#    - last_login_at update
#
# 3. Auth response builder
#    - Access token inclusion
#    - Optional message inclusion
#    - Profile initial generation
#
# NOTE:
#
# - JWT internals are tested separately.
# - Login/refresh/logout flows are tested separately.
# - This file focuses ONLY on session orchestration.
#
# =========================================================

from sqlmodel import select

from app.core.enums import (
    AuthProviderType,
    UserRole,
)

from uuid import UUID

from app.models.auth.auth_provider import AuthProvider
from app.models.auth.refresh_session import RefreshSession
from app.models.auth.user import User

from app.services.auth.auth_sessions import (
    build_auth_response,
    create_refresh_session,
    create_user_auth_session,
)

from app.services.auth.password_service import (
    hash_password,
    verify_password,
)

# =========================================================
# Helpers
# =========================================================


def create_local_user(
    session,
    *,
    email="sessions@example.com",
    username="sessionuser",
):

    user = User(
        name="Session User",
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


# =========================================================
# create_refresh_session
# =========================================================


def test_create_refresh_session(
    session,
):

    user = create_local_user(
        session,
    )

    (
        refresh_token,
        refresh_session,
    ) = create_refresh_session(
        user.id,
    )

    assert refresh_token is not None

    assert refresh_session.id is not None

    assert refresh_session.user_id == user.id

    assert refresh_session.token_hash != refresh_token

    assert verify_password(
        refresh_token,
        refresh_session.token_hash,
    )

    assert refresh_session.expires_at is not None


# =========================================================
# create_user_auth_session
# =========================================================


def test_create_user_auth_session(
    session,
):

    user = create_local_user(
        session,
    )

    assert user.last_login_at is None

    (
        access_token,
        refresh_token,
    ) = create_user_auth_session(
        session,
        user,
    )

    session.commit()

    assert access_token is not None

    assert refresh_token is not None

    updated_user = session.get(
        User,
        user.id,
    )

    assert updated_user.last_login_at is not None

    refresh_session = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
        )
    ).first()

    assert refresh_session is not None

    assert verify_password(
        refresh_token,
        refresh_session.token_hash,
    )


# =========================================================
# build_auth_response
# =========================================================


def test_build_auth_response_with_access_token():
    
    user = User(
        id=UUID("12345678-1234-1234-1234-123456789012"),
        name="Varun",
        username="varun",
        email="varun@example.com",
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
    )

    response = build_auth_response(
        user,
        access_token="access-token",
        message="Login successful",
    )

    assert response["message"] == "Login successful"

    assert response["access_token"] == "access-token"

    assert response["token_type"] == "bearer"

    assert response["user"]["name"] == "Varun"

    assert response["user"]["profile_initial"] == "V"


def test_build_auth_response_without_access_token():

    user = User(
        id=UUID("12345678-1234-1234-1234-123456789012"),
        name="Aureon User",
        username="aureon",
        email="aureon@example.com",
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
    )

    response = build_auth_response(
        user,
    )

    assert "access_token" not in response

    assert "token_type" not in response

    assert "message" not in response

    assert response["user"]["profile_initial"] == "A"