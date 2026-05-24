# =========================================================
# OAuth Service Flow Tests
# =========================================================
#
# This file tests:
#
# - handle_google_auth_callback()
# - handle_complete_oauth_signup()
#
# Covered areas:
#
# 1. Existing Google OAuth login
#    - Existing provider login
#    - Session creation
#
# 2. New OAuth onboarding flow
#    - OAuth signup token generation
#    - Onboarding response
#
# 3. Existing local account linking
#    - Google provider attachment
#    - Existing account login
#
# 4. Guest upgrade via Google OAuth
#    - Guest conversion
#    - Google provider attachment
#
# 5. OAuth signup completion
#    - New OAuth user creation
#    - Auth provider creation
#    - Session creation
#
# 6. Validation protections
#    - Invalid Google payload rejection
#    - Unverified email rejection
#    - Invalid OAuth token rejection
#    - Invalid OAuth payload rejection
#    - Invalid public role rejection
#    - Existing account collision rejection
#
# NOTE:
#
# - Route redirect behavior is NOT tested here.
# - This file focuses ONLY on service logic + DB state.
#
# =========================================================

import pytest

from sqlmodel import select

from app.core.enums import (
    AuthProviderType,
    UserRole,
)

from app.core.exceptions.auth import (
    AuthError,
)

from app.models.auth.auth_provider import AuthProvider
from app.models.auth.refresh_session import RefreshSession
from app.models.auth.user import User

from app.services.auth.oauth_service import (
    handle_complete_oauth_signup,
    handle_google_auth_callback,
)

from app.services.auth.auth_tokens import (
    create_oauth_signup_token,
)

from app.services.auth.password_service import (
    generate_unusable_password_hash,
)

GOOGLE_PROVIDER = AuthProviderType.GOOGLE.value


# =========================================================
# Existing Google OAuth Login
# =========================================================


def test_google_auth_existing_oauth_login(
    session,
):

    user = User(
        name="OAuth User",
        username="oauthuser",
        username_normalized="oauthuser",
        email="oauth@example.com",
        password_hash=generate_unusable_password_hash(),
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
    )

    session.add(user)
    session.flush()

    provider = AuthProvider(
        user_id=user.id,
        provider=GOOGLE_PROVIDER,
        provider_user_id="google-user-id",
    )

    session.add(provider)
    session.commit()

    result = handle_google_auth_callback(
        session,
        google_user_id="google-user-id",
        email="oauth@example.com",
        name="OAuth User",
        email_verified=True,
    )

    assert result["type"] == "login"

    assert result["user"] == user

    refresh_session = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
        )
    ).first()

    assert refresh_session is not None


# =========================================================
# New OAuth Onboarding
# =========================================================


def test_google_auth_new_oauth_onboarding(
    session,
):

    result = handle_google_auth_callback(
        session,
        google_user_id="new-google-id",
        email="newoauth@example.com",
        name="New OAuth",
        email_verified=True,
    )

    assert result["type"] == "onboarding"

    assert "oauth_signup_token" in result

    assert result["email"] == "newoauth@example.com"

    assert result["name"] == "New OAuth"


# =========================================================
# Existing Local Account Linking
# =========================================================


def test_google_auth_existing_local_account_linking(
    session,
):

    local_user = User(
        name="Local User",
        username="localuser",
        username_normalized="localuser",
        email="local@example.com",
        password_hash="hashed_password",
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
    )

    session.add(local_user)
    session.flush()

    local_provider = AuthProvider(
        user_id=local_user.id,
        provider=AuthProviderType.LOCAL.value,
        provider_user_id="local@example.com",
    )

    session.add(local_provider)
    session.commit()

    result = handle_google_auth_callback(
        session,
        google_user_id="google-link-id",
        email="local@example.com",
        name="Local User",
        email_verified=True,
    )

    assert result["type"] == "login"

    provider = session.exec(
        select(AuthProvider).where(
            AuthProvider.user_id == local_user.id,
            AuthProvider.provider == GOOGLE_PROVIDER,
        )
    ).first()

    assert provider is not None

    assert provider.provider_user_id == "google-link-id"


# =========================================================
# Guest Upgrade Flow
# =========================================================


def test_google_auth_guest_upgrade_success(
    session,
):

    guest_user = User(
        name="Guest",
        username=None,
        username_normalized=None,
        email=None,
        password_hash=None,
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=True,
        profile_color="#ffffff",
    )

    session.add(guest_user)
    session.commit()

    result = handle_google_auth_callback(
        session,
        google_user_id="guest-google-id",
        email="guest@example.com",
        name="Guest User",
        email_verified=True,
        current_user=guest_user,
    )

    assert result["type"] == "login"

    updated_user = session.get(
        User,
        guest_user.id,
    )

    assert updated_user is not None

    assert updated_user.is_guest is False

    assert updated_user.email == "guest@example.com"

    provider = session.exec(
        select(AuthProvider).where(
            AuthProvider.user_id == updated_user.id,
            AuthProvider.provider == GOOGLE_PROVIDER,
        )
    ).first()

    assert provider is not None


# =========================================================
# OAuth Signup Completion
# =========================================================


def test_complete_oauth_signup_success(
    session,
):

    oauth_signup_token = create_oauth_signup_token(
        {
            "sub": "completeoauth@example.com",
            "name": "Complete OAuth",
            "google_user_id": "complete-google-id",
        }
    )

    (
        user,
        access_token,
        refresh_token,
    ) = handle_complete_oauth_signup(
        session,
        oauth_signup_token=oauth_signup_token,
        role=UserRole.LISTENER.value,
    )

    assert user.email == "completeoauth@example.com"

    assert user.username is not None

    assert access_token is not None

    assert refresh_token is not None

    provider = session.exec(
        select(AuthProvider).where(
            AuthProvider.user_id == user.id,
        )
    ).first()

    assert provider is not None

    assert provider.provider == GOOGLE_PROVIDER


# =========================================================
# Google Callback Validation
# =========================================================


def test_google_auth_invalid_google_data(
    session,
):

    with pytest.raises(AuthError) as exc:

        handle_google_auth_callback(
            session,
            google_user_id=None,
            email="invalid@example.com",
            name="Invalid",
            email_verified=True,
        )

    assert exc.value.code == "INVALID_GOOGLE_USER_DATA"


def test_google_auth_unverified_email(
    session,
):

    with pytest.raises(AuthError) as exc:

        handle_google_auth_callback(
            session,
            google_user_id="google-id",
            email="invalid@example.com",
            name="Invalid",
            email_verified=False,
        )

    assert exc.value.code == "GOOGLE_EMAIL_NOT_VERIFIED"


# =========================================================
# OAuth Signup Completion Validation
# =========================================================


def test_complete_oauth_signup_invalid_token(
    session,
):

    with pytest.raises(AuthError) as exc:

        handle_complete_oauth_signup(
            session,
            oauth_signup_token="invalid-token",
            role=UserRole.LISTENER.value,
        )

    assert exc.value.code == "INVALID_OAUTH_SIGNUP_TOKEN"


def test_complete_oauth_signup_invalid_public_role(
    session,
):

    oauth_signup_token = create_oauth_signup_token(
        {
            "sub": "role@example.com",
            "name": "Role User",
            "google_user_id": "role-google-id",
        }
    )

    with pytest.raises(AuthError) as exc:

        handle_complete_oauth_signup(
            session,
            oauth_signup_token=oauth_signup_token,
            role="admin",
        )

    assert exc.value.code == "INVALID_PUBLIC_ROLE"


def test_complete_oauth_signup_invalid_payload(
    session,
):

    oauth_signup_token = create_oauth_signup_token(
        {
            "sub": "broken@example.com",
        }
    )

    with pytest.raises(AuthError) as exc:

        handle_complete_oauth_signup(
            session,
            oauth_signup_token=oauth_signup_token,
            role=UserRole.LISTENER.value,
        )

    assert exc.value.code == "INVALID_OAUTH_SIGNUP_PAYLOAD"


def test_complete_oauth_signup_existing_account(
    session,
):

    existing_user = User(
        name="Existing",
        username="existing",
        username_normalized="existing",
        email="existingoauth@example.com",
        password_hash="hashed",
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
    )

    session.add(existing_user)
    session.commit()

    oauth_signup_token = create_oauth_signup_token(
        {
            "sub": "existingoauth@example.com",
            "name": "Existing",
            "google_user_id": "existing-google-id",
        }
    )

    with pytest.raises(AuthError) as exc:

        handle_complete_oauth_signup(
            session,
            oauth_signup_token=oauth_signup_token,
            role=UserRole.LISTENER.value,
        )

    assert exc.value.code == "ACCOUNT_ALREADY_EXISTS"
