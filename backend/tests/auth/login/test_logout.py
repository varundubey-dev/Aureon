# =========================================================
# Logout Flow Tests
# =========================================================
#
# This file tests:
#
# /auth/logout
#
# Covered areas:
#
# 1. Successful logout flow
#    - Refresh session deletion
#    - Cookie clearing behavior
#
# 2. Safe logout protections
#    - Missing refresh token handling
#    - Invalid refresh token handling
#    - Invalid session handling
#
# NOTE:
#
# - Logout should NEVER fail publicly.
# - Even invalid/missing tokens return success.
# - Access token invalidation is NOT handled here.
#
# =========================================================

from sqlmodel import select

from app.core.enums import (
    AuthProviderType,
    UserRole,
)

from app.models.auth.auth_provider import AuthProvider
from app.models.auth.refresh_session import RefreshSession
from app.models.auth.user import User

from app.services.auth.auth_sessions import (
    create_user_auth_session,
)

from app.services.auth.auth_tokens import (
    create_refresh_token,
)

from app.services.auth.password_service import (
    hash_password,
)

# =========================================================
# Helpers
# =========================================================


def create_local_user(
    session,
    *,
    email="logout@example.com",
    username="logoutuser",
):

    user = User(
        name="Logout User",
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


def create_authenticated_refresh_token(
    session,
):

    user = create_local_user(
        session,
    )

    (
        access_token,
        refresh_token,
    ) = create_user_auth_session(
        session,
        user,
    )

    session.commit()

    return (
        user,
        refresh_token,
    )


def logout(
    client,
    refresh_token=None,
):

    client.cookies.clear()

    if refresh_token:

        client.cookies.set(
            "refresh_token",
            refresh_token,
        )

    return client.post(
        "/api/v1/auth/logout",
    )


# =========================================================
# Successful Logout Flow
# =========================================================


def test_logout_success(
    client,
    session,
):

    (
        user,
        refresh_token,
    ) = create_authenticated_refresh_token(
        session,
    )

    refresh_session = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
        )
    ).first()

    assert refresh_session is not None

    response = logout(
        client,
        refresh_token,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "logged_out"

    assert data["message"] == "Logout successful"

    deleted_session = session.get(
        RefreshSession,
        refresh_session.id,
    )

    assert deleted_session is None

    cookies = response.headers.get(
        "set-cookie",
        "",
    ).lower()

    assert "refresh_token=" in cookies


# =========================================================
# Safe Logout Protections
# =========================================================


def test_logout_missing_refresh_token(
    client,
):

    response = logout(
        client,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "logged_out"


def test_logout_invalid_refresh_token(
    client,
):

    response = logout(
        client,
        "invalid-token",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "logged_out"


def test_logout_invalid_refresh_session(
    client,
    session,
):

    user = create_local_user(
        session,
    )

    fake_refresh_token, _ = create_refresh_token(
        str(user.id),
        "11111111-1111-1111-1111-111111111111",
    )

    response = logout(
        client,
        fake_refresh_token,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "logged_out"
