# =========================================================
# Local Signup E2E Flow Tests
# =========================================================
#
# This file tests:
#
# /api/v1/auth/signup/request
# /api/v1/auth/signup/verify
# /api/v1/auth/signup/session/{token}
# /api/v1/auth/signup/complete
# /api/v1/auth/login
# /api/v1/auth/refresh
# /api/v1/auth/logout
#
# Covered areas:
#
# 1. Complete local signup flow
#    - Signup request
#    - OTP verification
#    - Signup session validation
#    - Account completion
#
# 2. Login flow
#    - Email login
#    - Username login
#
# 3. Session lifecycle
#    - Refresh
#    - Logout
#
# 4. Database integrity
#    - User creation
#    - Auth provider creation
#    - OTP cleanup
#    - Pending signup cleanup
#    - Refresh session creation
#
# NOTE:
#
# - JWT internals are NOT tested here.
# - OTP hashing internals are NOT tested here.
# - Refresh token internals are tested separately.
#
# =========================================================

from sqlmodel import select

from app.core.enums import (
    AuthProviderType,
    UserRole,
)

from app.models.auth.auth_provider import (
    AuthProvider,
)

from app.models.auth.otp import (
    OTP,
)

from app.models.auth.pending_signup import (
    PendingSignup,
)

from app.models.auth.refresh_session import (
    RefreshSession,
)

from app.models.auth.user import (
    User,
)

from tests.e2e.helpers.auth_login_handlers import (
    login,
)

from tests.e2e.helpers.auth_session_handlers import (
    logout,
    refresh_auth_session,
)

from tests.e2e.helpers.auth_signup_handlers import (
    complete_signup,
    signup_request,
    validate_signup_session,
    verify_signup_otp,
)

from tests.e2e.utils.otp_utils import (
    extract_otp,
)

# =========================================================
# Full E2E Flow
# =========================================================


def test_complete_local_signup_login_refresh_logout_flow(
    client,
    session,
    mock_send_email,
):
    """
    Complete authentication lifecycle E2E test.
    """

    email = "varun@example.com"
    name = "Varun"
    username = "varunmusic"
    password = "StrongPass123!"
    role = UserRole.LISTENER.value

    # =====================================================
    # Step 1 — Signup Request
    # =====================================================

    signup_response = signup_request(
        client,
        email=email,
        name=name,
    )

    assert signup_response.status_code == 200

    signup_data = signup_response.json()

    assert signup_data["type"] == "otp_verification"

    assert signup_data["message"] == "OTP sent successfully"

    # =====================================================
    # Step 2 — Email Sent
    # =====================================================

    assert mock_send_email["signup"].call_count == 1

    sent_email = mock_send_email["signup"].call_args_list[0].kwargs

    assert sent_email["recipient"] == email
    assert sent_email["subject"] == "Aureon Signup OTP"

    otp = extract_otp(
        sent_email["body"],
    )

    # =====================================================
    # Step 3 — Verify OTP
    # =====================================================

    verify_response = verify_signup_otp(
        client,
        email=email,
        otp=otp,
    )

    assert verify_response.status_code == 200

    verify_data = verify_response.json()

    assert verify_data["message"] == "OTP verified successfully"

    assert verify_data["type"] == "normal_signup"

    signup_token = verify_data["signup_token"]

    assert signup_token is not None

    assert isinstance(
        verify_data["username_suggestions"],
        list,
    )

    # =====================================================
    # Step 4 — Validate Signup Session
    # =====================================================

    session_response = validate_signup_session(
        client,
        signup_token=signup_token,
    )

    assert session_response.status_code == 200

    session_data = session_response.json()

    assert session_data["message"] == "Signup session valid"

    assert session_data["email"] == email

    assert session_data["name"] == name

    assert session_data["type"] == "normal_signup"

    # =====================================================
    # Step 5 — Complete Signup
    # =====================================================

    complete_response = complete_signup(
        client,
        signup_token=signup_token,
        username=username,
        password=password,
        role=role,
    )

    assert complete_response.status_code == 200

    complete_data = complete_response.json()

    assert complete_data["message"] == "Signup completed successfully"

    # =====================================================
    # Step 6 — Refresh Cookie Created
    # =====================================================

    set_cookie_header = complete_response.headers.get(
        "set-cookie",
        "",
    )

    assert "refresh_token=" in set_cookie_header

    # =====================================================
    # Step 7 — User Created
    # =====================================================

    user = session.exec(
        select(User).where(
            User.email == email,
        ),
    ).first()

    assert user is not None

    assert user.name == name

    assert user.username == username

    assert user.email == email

    assert user.role == role

    assert user.password_hash is not None

    # =====================================================
    # Step 8 — Auth Provider Created
    # =====================================================

    provider = session.exec(
        select(AuthProvider).where(
            AuthProvider.user_id == user.id,
        ),
    ).first()

    assert provider is not None

    assert provider.provider == AuthProviderType.LOCAL.value

    assert provider.provider_user_id == email

    # =====================================================
    # Step 9 — OTP Cleanup
    # =====================================================

    otp_record = session.exec(
        select(OTP).where(
            OTP.email == email,
        ),
    ).first()

    assert otp_record is None

    # =====================================================
    # Step 10 — Pending Signup Cleanup
    # =====================================================

    pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == email,
        ),
    ).first()

    assert pending_signup is None

    # =====================================================
    # Step 11 — Refresh Session Created
    # =====================================================

    refresh_session = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
        ),
    ).first()

    assert refresh_session is not None

    # =====================================================
    # Step 12 — Logout
    # =====================================================

    logout_response = logout(
        client,
    )

    assert logout_response.status_code == 200

    logout_cookie = logout_response.headers.get(
        "set-cookie",
        "",
    )

    assert "refresh_token=" in logout_cookie

    # =====================================================
    # Step 13 — Refresh Should Fail
    # =====================================================

    refresh_response = refresh_auth_session(
        client,
    )

    assert refresh_response.status_code in (
        401,
        403,
    )

    # =====================================================
    # Step 14 — Login Using Email
    # =====================================================

    email_login_response = login(
        client,
        identifier=email,
        password=password,
    )

    if email_login_response.status_code != 200:
        print(email_login_response.json())

    assert email_login_response.status_code == 200

    email_login_data = email_login_response.json()

    assert email_login_data["user"]["email"] == email

    assert email_login_data["user"]["username"] == username

    email_login_cookie = email_login_response.headers.get(
        "set-cookie",
        "",
    )

    assert "refresh_token=" in email_login_cookie

    # =====================================================
    # Step 15 — Refresh After Login Works
    # =====================================================

    refresh_response = refresh_auth_session(
        client,
    )

    assert refresh_response.status_code == 200

    refresh_data = refresh_response.json()

    assert refresh_data["user"]["email"] == email

    # =====================================================
    # Step 16 — Logout Again
    # =====================================================

    second_logout_response = logout(
        client,
    )

    assert second_logout_response.status_code == 200

    # =====================================================
    # Step 17 — Login Using Username
    # =====================================================

    username_login_response = login(
        client,
        identifier=username,
        password=password,
    )

    if username_login_response.status_code != 200:
        print(username_login_response.json())

    assert username_login_response.status_code == 200

    username_login_data = username_login_response.json()

    assert username_login_data["user"]["email"] == email

    assert username_login_data["user"]["username"] == username

    username_login_cookie = username_login_response.headers.get(
        "set-cookie",
        "",
    )

    assert "refresh_token=" in username_login_cookie
