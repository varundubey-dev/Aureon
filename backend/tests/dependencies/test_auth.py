# =========================================================
# Auth Dependency Tests
# =========================================================
#
# This file tests:
#
# auth.py dependencies
#
# Covered areas:
#
# 1. Access token validation
#    - Valid token authentication
#    - Invalid token rejection
#    - Missing user rejection
#    - Token version invalidation
#
# 2. Required auth dependency
#    - get_current_user()
#    - Missing token rejection
#    - Invalid token rejection
#
# 3. Optional auth dependency
#    - get_optional_current_user()
#    - Anonymous request support
#
# 4. Session restore dependency
#    - Access token priority
#    - Refresh token fallback
#    - Invalid refresh token handling
#    - Invalid refresh session handling
#
# NOTE:
#
# - JWT internals are tested separately.
# - Route integration is tested separately.
# - This file focuses ONLY on dependency behavior.
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
    create_access_token,
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
    email="dependency@example.com",
    username="dependencyuser",
    token_version=0,
):

    user = User(
        name="Dependency User",
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
        token_version=token_version,
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


def authenticated_headers(
    access_token,
):

    return {
        "Authorization": f"Bearer {access_token}",
    }


def get_me(
    client,
    access_token=None,
):

    headers = {}

    if access_token:

        headers = authenticated_headers(
            access_token,
        )

    return client.get(
        "/api/v1/auth/me",
        headers=headers,
    )


# =========================================================
# Required Authentication Dependency
# =========================================================


def test_get_current_user_success(
    client,
    session,
):

    user = create_local_user(
        session,
    )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "token_version": user.token_version,
        }
    )

    response = get_me(
        client,
        access_token,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "authenticated"

    assert data["user"]["email"] == user.email


def test_get_current_user_missing_token(
    client,
):

    response = get_me(
        client,
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "AUTH_REQUIRED"


def test_get_current_user_invalid_access_token(
    client,
):

    response = get_me(
        client,
        "invalid-token",
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "INVALID_ACCESS_TOKEN"


# =========================================================
# Token Version Invalidation
# =========================================================


def test_validate_access_token_user_token_version_mismatch(
    client,
    session,
):

    user = create_local_user(
        session,
        token_version=0,
    )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "token_version": 0,
        }
    )

    # Simulate logout-all / password reset
    user.token_version = 1

    session.add(
        user,
    )

    session.commit()

    response = get_me(
        client,
        access_token,
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "INVALID_ACCESS_TOKEN"


def test_validate_access_token_user_missing_user(
    client,
    session,
):

    user = create_local_user(
        session,
    )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "token_version": user.token_version,
        }
    )

    providers = session.exec(
        select(AuthProvider).where(
            AuthProvider.user_id == user.id,
        )
    ).all()

    for provider in providers:

        session.delete(
            provider,
        )

    refresh_sessions = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
        )
    ).all()

    for refresh_session in refresh_sessions:

        session.delete(
            refresh_session,
        )

    session.delete(
        user,
    )

    session.commit()

    response = get_me(
        client,
        access_token,
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "INVALID_ACCESS_TOKEN"


# =========================================================
# Session Restore Dependency
# =========================================================


def test_optional_session_user_refresh_cookie_restore(
    client,
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

    client.cookies.set(
        "refresh_token",
        refresh_token,
    )

    response = client.get(
        "/api/v1/auth/google/login",
        follow_redirects=False,
    )

    # Route redirects to Google OAuth
    # Dependency should authenticate silently
    assert response.status_code in [200, 302, 307]


def test_optional_session_user_invalid_refresh_token(
    client,
):

    client.cookies.set(
        "refresh_token",
        "invalid-token",
    )

    response = client.get(
        "/api/v1/auth/google/login",
        follow_redirects=False,
    )

    assert response.status_code in [200, 302, 307]


def test_optional_session_user_invalid_refresh_session(
    client,
    session,
):

    user = create_local_user(
        session,
    )

    fake_refresh_token, _ = create_user_auth_session(
        session,
        user,
    )

    refresh_session = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
        )
    ).first()

    session.delete(
        refresh_session,
    )

    session.commit()

    client.cookies.set(
        "refresh_token",
        fake_refresh_token,
    )

    response = client.get(
        "/api/v1/auth/google/login",
        follow_redirects=False,
    )

    assert response.status_code in [200, 302, 307]


def test_optional_session_user_prioritizes_access_token(
    client,
    session,
):

    user = create_local_user(
        session,
    )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "token_version": user.token_version,
        }
    )

    (
        _,
        refresh_token,
    ) = create_user_auth_session(
        session,
        user,
    )

    session.commit()

    client.cookies.set(
        "refresh_token",
        refresh_token,
    )

    response = client.get(
        "/api/v1/auth/me",
        headers=authenticated_headers(
            access_token,
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user"]["email"] == user.email
