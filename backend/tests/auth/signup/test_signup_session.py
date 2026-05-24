# =========================================================
# Signup Session Validation Flow Tests
# =========================================================
#
# This file tests: Complete signup/session/{signup_token} API flow
#
# validate_signup_session()
#
# Covered areas:
#
# 1. Successful signup session validation
#    - Valid signup token acceptance
#    - Pending signup retrieval
#    - Username suggestion generation
#    - Response payload correctness
#
# 2. Signup session protections
#    - Invalid token rejection
#    - Missing pending signup detection
#    - Unverified signup rejection
#
# 3. OAuth-first signup session flow
#    - Existing OAuth account detection
#    - complete_local_setup response type
#
# NOTE:
#
# - This file ONLY validates temporary signup session state.
# - It does NOT test account creation.
# - It does NOT test OTP verification itself.
# - OAuth-first behavior here only affects response type.
#
# =========================================================

from sqlmodel import select

from app.core.enums import (
    AuthProviderType,
    UserRole,
)

from app.models.auth.auth_provider import AuthProvider
from app.models.auth.otp import OTP
from app.models.auth.pending_signup import PendingSignup
from app.models.auth.user import User

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


# =========================================================
# Success Flow
# =========================================================


def test_validate_signup_session_success(
    client,
    session,
):

    email = "session@example.com"

    signup_token = create_verified_signup_state(
        client,
        session,
        email=email,
    )

    response = client.get(
        f"/api/v1/auth/signup/session/{signup_token}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "normal_signup"

    assert data["email"] == email

    assert data["name"] == "Varun"

    assert isinstance(
        data["username_suggestions"],
        list,
    )


# =========================================================
# Session Validation Protections
# =========================================================


def test_validate_signup_session_invalid_token(
    client,
):

    response = client.get(
        "/api/v1/auth/signup/session/invalid-token",
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "INVALID_SIGNUP_SESSION"


def test_validate_signup_session_missing_pending_signup(
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

    response = client.get(
        f"/api/v1/auth/signup/session/{signup_token}",
    )

    assert response.status_code == 404

    data = response.json()

    assert data["code"] == "PENDING_SIGNUP_NOT_FOUND"


def test_validate_signup_session_unverified_signup(
    client,
    session,
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

    response = client.get(
        f"/api/v1/auth/signup/session/{signup_token}",
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "SIGNUP_VERIFICATION_REQUIRED"


# =========================================================
# OAuth-first Flow
# =========================================================


def test_validate_signup_session_oauth_first_flow(
    client,
    session,
):

    oauth_user = User(
        name="OAuth User",
        username=None,
        username_normalized=None,
        email="oauthsession@example.com",
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
        email="oauthsession@example.com",
        name="OAuth User",
    )

    response = client.get(
        f"/api/v1/auth/signup/session/{signup_token}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["type"] == "complete_local_setup"
