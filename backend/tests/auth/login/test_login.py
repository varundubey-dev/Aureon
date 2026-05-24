# =========================================================
# Login Flow Tests
# =========================================================
#
# This file tests:
#
# /auth/login
#
# Covered areas:
#
# 1. Successful login flow
#    - Email login
#    - Username login
#    - Access token creation
#    - Refresh session creation
#    - Refresh cookie creation
#
# 2. Credential protections
#    - Invalid password rejection
#    - Nonexistent account rejection
#
# 3. Provider protections
#    - OAuth-only account rejection
#    - Missing password rejection
#
# NOTE:
#
# - Refresh token lifecycle is tested separately.
# - Logout behavior is tested separately.
# - JWT internals are NOT tested here.
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

from app.services.auth.password_service import (
    hash_password,
)

# =========================================================
# Helpers
# =========================================================


def create_local_user(
    session,
    *,
    name="Varun",
    username="varun",
    email="varun@example.com",
    password="StrongPassword123!",
):

    user = User(
        name=name,
        username=username,
        username_normalized=username,
        email=email,
        password_hash=hash_password(password),
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


def login(
    client,
    *,
    identifier,
    password,
):

    return client.post(
        "/api/v1/auth/login",
        json={
            "identifier": identifier,
            "password": password,
        },
    )


# =========================================================
# Successful Login
# =========================================================


def test_login_with_email_success(
    client,
    session,
):

    user = create_local_user(
        session,
    )

    response = login(
        client,
        identifier=user.email,
        password="StrongPassword123!",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "authenticated"

    assert data["user"]["email"] == user.email

    assert data["access_token"] is not None

    refresh_session = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
        )
    ).first()

    assert refresh_session is not None

    cookies = response.cookies

    assert "refresh_token" in cookies


def test_login_with_username_success(
    client,
    session,
):

    user = create_local_user(
        session,
    )

    response = login(
        client,
        identifier=user.username,
        password="StrongPassword123!",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "authenticated"

    assert data["user"]["username"] == user.username

    assert data["access_token"] is not None


# =========================================================
# Invalid Credentials
# =========================================================


def test_login_invalid_password(
    client,
    session,
):

    create_local_user(
        session,
    )

    response = login(
        client,
        identifier="varun@example.com",
        password="WrongPassword123!",
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "INVALID_CREDENTIALS"


def test_login_nonexistent_account(
    client,
):

    response = login(
        client,
        identifier="missing@example.com",
        password="StrongPassword123!",
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "INVALID_CREDENTIALS"


# =========================================================
# OAuth-only Account Protections
# =========================================================


def test_login_oauth_only_account(
    client,
    session,
):

    oauth_user = User(
        name="OAuth User",
        username="oauthuser",
        username_normalized="oauthuser",
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
        provider_user_id="google-oauth-id",
    )

    session.add(provider)
    session.commit()

    response = login(
        client,
        identifier="oauth@example.com",
        password="StrongPassword123!",
    )

    assert response.status_code == 403

    data = response.json()

    assert data["code"] == "SOCIAL_LOGIN_REQUIRED"


def test_login_password_unavailable(
    client,
    session,
):

    user = User(
        name="Broken User",
        username="brokenuser",
        username_normalized="brokenuser",
        email="broken@example.com",
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
        provider=AuthProviderType.LOCAL.value,
        provider_user_id="broken@example.com",
    )

    session.add(provider)
    session.commit()

    response = login(
        client,
        identifier="broken@example.com",
        password="StrongPassword123!",
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "PASSWORD_LOGIN_UNAVAILABLE"
