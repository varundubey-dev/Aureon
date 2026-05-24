# =========================================================
# Refresh Token Flow Tests
# =========================================================
#
# This file tests:
#
# /auth/refresh
#
# Covered areas:
#
# 1. Successful refresh flow
#    - Access token regeneration
#    - Existing refresh token reuse
#    - Sliding refresh renewal
#
# 2. Refresh token protections
#    - Missing refresh token rejection
#    - Invalid refresh token rejection
#    - Invalid refresh session rejection
#    - User mismatch rejection
#    - Expired refresh session rejection
#
# 3. Refresh session behavior
#    - Expired session cleanup
#    - Sliding expiration updates
#
# NOTE:
#
# - Login flow is tested separately.
# - Logout flow is tested separately.
# - JWT payload internals are NOT tested here.
# - USER_NOT_FOUND branch is intentionally NOT tested
#   because DB foreign key constraints prevent the
#   invalid state from existing naturally.
#
# =========================================================

from datetime import timedelta

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

from app.utils.datetime import (
    get_utc_now,
)

# =========================================================
# Helpers
# =========================================================


def create_local_user(
    session,
    *,
    email="refresh@example.com",
    username="refreshuser",
):

    user = User(
        name="Refresh User",
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


def refresh(
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
        "/api/v1/auth/refresh",
    )


# =========================================================
# Successful Refresh Flow
# =========================================================


def test_refresh_token_success(
    client,
    session,
):

    (
        user,
        refresh_token,
    ) = create_authenticated_refresh_token(
        session,
    )

    response = refresh(
        client,
        refresh_token,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "authenticated"

    assert data["user"]["email"] == user.email

    assert data["access_token"] is not None


def test_refresh_token_sliding_renewal(
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

    refresh_session.expires_at = get_utc_now() + timedelta(days=5)

    session.add(
        refresh_session,
    )

    session.commit()

    old_hash = refresh_session.token_hash

    response = refresh(
        client,
        refresh_token,
    )

    assert response.status_code == 200

    updated_session = session.get(
        RefreshSession,
        refresh_session.id,
    )

    assert updated_session.token_hash != old_hash

    cookies = response.cookies

    assert "refresh_token" in cookies


def test_refresh_token_keeps_same_token_when_not_near_expiry(
    client,
    session,
):

    (
        user,
        refresh_token,
    ) = create_authenticated_refresh_token(
        session,
    )

    response = refresh(
        client,
        refresh_token,
    )

    assert response.status_code == 200

    cookies = response.cookies

    # No replacement cookie should be set

    assert "refresh_token" not in cookies


# =========================================================
# Missing / Invalid Token Protections
# =========================================================


def test_refresh_token_missing(
    client,
):

    response = refresh(
        client,
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "REFRESH_TOKEN_MISSING"


def test_refresh_token_invalid(
    client,
):

    response = refresh(
        client,
        "invalid-token",
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "INVALID_REFRESH_TOKEN"


# =========================================================
# Refresh Session Protections
# =========================================================


def test_refresh_token_invalid_refresh_session(
    client,
    session,
):

    user = create_local_user(
        session,
    )

    refresh_token, _ = create_refresh_token(
        str(user.id),
        "11111111-1111-1111-1111-111111111111",
    )

    response = refresh(
        client,
        refresh_token,
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "INVALID_REFRESH_SESSION"


def test_refresh_token_user_mismatch(
    client,
    session,
):

    user_1 = create_local_user(
        session,
        email="user1@example.com",
        username="user1",
    )

    user_2 = create_local_user(
        session,
        email="user2@example.com",
        username="user2",
    )

    (
        access_token,
        refresh_token,
    ) = create_user_auth_session(
        session,
        user_1,
    )

    session.commit()

    refresh_session = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == user_1.id,
        )
    ).first()

    fake_refresh_token, _ = create_refresh_token(
        str(user_2.id),
        str(refresh_session.id),
    )

    response = refresh(
        client,
        fake_refresh_token,
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "INVALID_REFRESH_SESSION"


def test_refresh_token_expired(
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

    refresh_session.expires_at = get_utc_now() - timedelta(days=32)

    session.add(
        refresh_session,
    )

    session.commit()

    response = refresh(
        client,
        refresh_token,
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "REFRESH_TOKEN_EXPIRED"

    deleted_session = session.get(
        RefreshSession,
        refresh_session.id,
    )

    assert deleted_session is None
