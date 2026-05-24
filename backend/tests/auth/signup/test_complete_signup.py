# =========================================================
# Complete Signup Flow Tests
# =========================================================
#
# This file tests: Complete /signup/complete API flow
#
# handle_complete_signup()
#
# Covered areas:
#
# 1. Fresh local account creation
#    - User creation
#    - Auth provider creation
#    - Session token creation
#    - Pending signup cleanup
#    - OTP cleanup
#
# 2. Signup token protections
#    - Invalid token rejection
#    - Missing pending signup detection
#    - Unverified signup rejection
#
# 3. Username validation protections
#    - Invalid username rejection
#    - Username collision rejection
#    - Username normalization behavior
#
# 4. Password validation protections
#    - Password mismatch rejection
#    - Weak password rejection
#
# 5. Role validation protections
#    - Invalid public role rejection
#
# 6. OAuth-first account completion
#    - Existing OAuth account upgrade
#    - Local auth provider attachment
#    - Password setup
#    - Username setup
#    - complete_local_setup flow
#
# 7. Guest upgrade flow
#    - Guest account upgrade
#    - Listener-only restriction
#    - Existing guest retrieval
#    - Guest conversion behavior
#
# NOTE:
#
# - This file tests FINAL account creation.
# - OTP verification is assumed complete here.
# - Session token validity is assumed.
#
# =========================================================

from sqlmodel import select
import pytest

from app.core.enums import (
    AuthProviderType,
    UserRole,
)

from app.models.auth.auth_provider import AuthProvider
from app.models.auth.otp import OTP
from app.models.auth.pending_signup import PendingSignup
from app.models.auth.refresh_session import RefreshSession
from app.models.auth.user import User

from datetime import timedelta

from app.utils.datetime import get_utc_now
from app.services.auth.otp_service import hash_otp

from app.services.auth.auth_tokens import (
    create_signup_token,
)

# =========================================================
# Helpers
# =========================================================


def create_verified_signup_state(
    client,
    session,
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

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    otp.verified = True

    pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == email,
        )
    ).first()

    pending_signup.verified = True

    session.add(otp)
    session.add(pending_signup)

    session.commit()

    return create_signup_token(
        email,
    )


def complete_signup(
    client,
    signup_token,
    username="varun",
    password="StrongPassword123!",
    confirm_password="StrongPassword123!",
    role="listener",
):

    return client.post(
        "/api/v1/auth/signup/complete",
        json={
            "signup_token": signup_token,
            "username": username,
            "password": password,
            "confirm_password": confirm_password,
            "role": role,
        },
    )


# =========================================================
# Fresh Local Signup Flow
# =========================================================


def test_complete_signup_success(
    client,
    session,
):

    email = "complete@example.com"

    signup_token = create_verified_signup_state(
        client,
        session,
        email=email,
    )

    response = complete_signup(
        client,
        signup_token,
    )

    assert response.status_code == 200

    user = session.exec(
        select(User).where(
            User.email == email,
        )
    ).first()

    assert user is not None

    assert user.username == "varun"

    assert user.role == "listener"

    assert user.is_guest is False

    auth_provider = session.exec(
        select(AuthProvider).where(AuthProvider.user_id == user.id)
    ).first()

    assert auth_provider is not None

    assert auth_provider.provider == AuthProviderType.LOCAL.value

    refresh_session = session.exec(
        select(RefreshSession).where(RefreshSession.user_id == user.id)
    ).first()

    assert refresh_session is not None

    pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == email,
        )
    ).first()

    otp = session.exec(
        select(OTP).where(
            OTP.email == email,
        )
    ).first()

    assert pending_signup is None
    assert otp is None


# =========================================================
# Signup Token Protections
# =========================================================


def test_complete_signup_invalid_signup_token(
    client,
):

    response = complete_signup(
        client,
        "invalid-token",
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "INVALID_SIGNUP_TOKEN"


def test_complete_signup_missing_pending_signup(
    client,
    session,
):

    email = "missingpending@example.com"

    signup_token = create_verified_signup_state(
        client,
        session,
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

    response = complete_signup(
        client,
        signup_token,
    )

    assert response.status_code == 404

    data = response.json()

    assert data["code"] == "PENDING_SIGNUP_NOT_FOUND"


def test_complete_signup_unverified_signup(
    client,
):

    email = "unverified@example.com"

    response = client.post(
        "/api/v1/auth/signup/request",
        json={
            "email": email,
            "name": "Varun",
        },
    )

    assert response.status_code == 200

    signup_token = create_signup_token(
        email,
    )

    response = complete_signup(
        client,
        signup_token,
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "SIGNUP_VERIFICATION_REQUIRED"


# =========================================================
# Username Validation
# =========================================================

@pytest.mark.parametrize(
    "invalid_username",
    [
        "A",
        "12345",
        "Test@123",
        "@@@",
        "!!Test",
        "",
        "   ",
        "Te@st",
    ],
)

def test_complete_signup_invalid_username(
    client,
    session,
    invalid_username,
):

    signup_token = create_verified_signup_state(
        client,
        session,
    )

    response = complete_signup(
        client,
        signup_token,
        invalid_username,
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "INVALID_USERNAME_FORMAT"


def test_complete_signup_username_taken(
    client,
    session,
):

    existing_user = User(
        name="Existing",
        username="takenuser",
        username_normalized="takenuser",
        email="existing@example.com",
        password_hash="hashed",
        role="listener",
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
    )

    session.add(existing_user)
    session.commit()

    signup_token = create_verified_signup_state(
        client,
        session,
    )

    response = complete_signup(
        client,
        signup_token,
        username="takenuser",
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "USERNAME_ALREADY_TAKEN"


# =========================================================
# Password Validation
# =========================================================


def test_complete_signup_password_mismatch(
    client,
    session,
):

    signup_token = create_verified_signup_state(
        client,
        session,
    )

    response = complete_signup(
        client,
        signup_token,
        password="StrongPassword123!",
        confirm_password="DifferentPassword123!",
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "PASSWORDS_DO_NOT_MATCH"

@pytest.mark.parametrize(
    "weak_password",
    [
        "A",
        "12345",
        "admin1235678",
        "@@@",
        "!!Test",
        "",
        "   ",
        "Te@st",
        "testpassword@123",
    ],
)

def test_complete_signup_weak_password(
    client,
    session,
    weak_password,
):

    signup_token = create_verified_signup_state(
        client,
        session,
    )

    response = complete_signup(
        client,
        signup_token,
        password=weak_password,
        confirm_password=weak_password,
    )

    assert response.status_code == 400

    data = response.json()

    assert data["code"] == "WEAK_PASSWORD"


# =========================================================
# Public Role Validation
# =========================================================


def test_complete_signup_invalid_public_role(
    client,
    session,
):

    signup_token = create_verified_signup_state(
        client,
        session,
    )

    response = complete_signup(
        client,
        signup_token,
        role="admin",
    )

    assert response.status_code == 403

    data = response.json()

    assert data["code"] == "INVALID_PUBLIC_ROLE"


# =========================================================
# OAuth-first Flow
# =========================================================


def test_complete_signup_oauth_first_flow(
    client,
    session,
):

    oauth_user = User(
        name="OAuth User",
        username=None,
        username_normalized=None,
        email="oauthcomplete@example.com",
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

    signup_token = create_verified_signup_state(
        client,
        session,
        email="oauthcomplete@example.com",
        name="OAuth User",
    )

    response = complete_signup(
        client,
        signup_token,
        username="oauthuser",
    )

    assert response.status_code == 200

    updated_user = session.exec(
        select(User).where(User.email == "oauthcomplete@example.com")
    ).first()

    assert updated_user.username == "oauthuser"

    assert updated_user.password_hash is not None

    providers = session.exec(
        select(AuthProvider).where(AuthProvider.user_id == updated_user.id)
    ).all()

    assert len(providers) == 2


# =========================================================
# Guest Upgrade Flow
# =========================================================


def test_complete_signup_guest_upgrade_success(
    client,
    session,
):

    guest_user = User(
        name="Guest",
        username=None,
        username_normalized=None,
        email=None,
        password_hash=None,
        role="listener",
        is_admin=False,
        is_guest=True,
        profile_color="#ffffff",
    )

    session.add(guest_user)
    session.commit()

    pending_signup = PendingSignup(
        name="Varun",
        email="guestupgrade@example.com",
        otp_hash=hash_otp("123456"),
        otp_expires_at=(get_utc_now() + timedelta(minutes=5)),
        verified=True,
        existing_user_id=guest_user.id,
    )

    session.add(pending_signup)
    session.commit()

    signup_token = create_signup_token(
        "guestupgrade@example.com",
    )

    response = complete_signup(
        client,
        signup_token,
        username="guestuser",
    )

    assert response.status_code == 200

    updated_user = session.get(
        User,
        guest_user.id,
    )

    assert updated_user.is_guest is False

    assert updated_user.email == "guestupgrade@example.com"

    assert updated_user.username == "guestuser"


def test_complete_signup_guest_upgrade_invalid_role(
    client,
    session,
):

    guest_user = User(
        name="Guest",
        username=None,
        username_normalized=None,
        email=None,
        password_hash=None,
        role="listener",
        is_admin=False,
        is_guest=True,
        profile_color="#ffffff",
    )

    session.add(guest_user)
    session.commit()

    pending_signup = PendingSignup(
        name="Varun",
        email="guestinvalid@example.com",
        otp_hash=hash_otp("123456"),
        otp_expires_at=(get_utc_now() + timedelta(minutes=5)),
        verified=True,
        existing_user_id=guest_user.id,
    )

    session.add(pending_signup)
    session.commit()

    signup_token = create_signup_token(
        "guestinvalid@example.com",
    )

    response = complete_signup(
        client,
        signup_token,
        username="guestinvalid",
        role="artist",
    )

    assert response.status_code == 403

    data = response.json()

    assert data["code"] == "INVALID_GUEST_UPGRADE_ROLE"