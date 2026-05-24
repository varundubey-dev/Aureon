# =========================================================
# OAuth First → Local Signup Upgrade E2E Tests
# =========================================================
#
# Flow:
#
# Existing Google OAuth account
# → Local signup request
# → OTP verification
# → Complete local setup
# → Role skipped
# → Local login works
# → Google login still works
#
# Covered areas:
#
# 1. OAuth-first account detection
# 2. OTP verification for local provider addition
# 3. Local credential setup
# 4. Existing role preservation
# 5. Local provider creation
# 6. Dual auth support
#    - password login
#    - Google OAuth login
#
# IMPORTANT:
#
# OAuth-first users should:
# - NOT select role again
# - keep existing role
# - add LOCAL provider
# - keep GOOGLE provider
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

from app.models.auth.pending_signup import (
    PendingSignup,
)

from app.models.auth.user import (
    User,
)

from app.services.auth.password_service import (
    generate_unusable_password_hash,
)

from tests.e2e.helpers.auth_login_handlers import (
    login,
)

from tests.e2e.helpers.auth_session_handlers import (
    logout,
    refresh_auth_session,
)

from tests.e2e.helpers.auth_oauth_handlers import (
    google_login,
    google_callback,
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
# OAuth Mock Fixture
# =========================================================



# =========================================================
# OAuth First → Local Upgrade Flow
# =========================================================


def test_oauth_first_local_signup_upgrade_flow(
    client,
    session,
    mock_google_oauth,
    mock_send_email,
):
    """
    OAuth-first account upgrades
    into full local + OAuth account.
    """

    email = mock_google_oauth["email"]

    google_user_id = mock_google_oauth["sub"]

    username = "varunmusic"

    password = "StrongPass123!"

    # =====================================================
    # Step 1 — Create Existing OAuth User
    # =====================================================

    oauth_user = User(
        name="Varun",
        username="varunoauth",
        username_normalized="varunoauth",
        email=email,
        password_hash=generate_unusable_password_hash(),
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
    )

    session.add(
        oauth_user,
    )

    session.commit()

    session.refresh(
        oauth_user,
    )

    # =====================================================
    # Step 2 — Existing Google Provider
    # =====================================================

    google_provider = AuthProvider(
        user_id=oauth_user.id,
        provider=AuthProviderType.GOOGLE.value,
        provider_user_id=google_user_id,
    )

    session.add(
        google_provider,
    )

    session.commit()

    # =====================================================
    # Step 3 — Local Signup Request
    # =====================================================

    signup_response = signup_request(
        client,
        email=email,
        name="Varun",
    )

    assert signup_response.status_code == 200

    signup_data = signup_response.json()

    # =====================================================
    # IMPORTANT ASSERTION
    # =====================================================

    assert (
        signup_data["type"]
        == "complete_local_setup"
    )

    # =====================================================
    # Step 4 — OTP Email Sent
    # =====================================================

    assert (
        mock_send_email["signup"].call_count
        == 1
    )

    sent_email = (
        mock_send_email["signup"]
        .call_args_list[0]
        .kwargs
    )

    otp = extract_otp(
        sent_email["body"],
    )

    # =====================================================
    # Step 5 — OTP Verification
    # =====================================================

    verify_response = verify_signup_otp(
        client,
        email=email,
        otp=otp,
    )

    assert verify_response.status_code == 200

    verify_data = verify_response.json()

    # =====================================================
    # IMPORTANT ASSERTION
    # =====================================================

    assert (
        verify_data["type"]
        == "complete_local_setup"
    )

    signup_token = verify_data[
        "signup_token"
    ]

    # =====================================================
    # Step 6 — Validate Signup Session
    # =====================================================

    session_response = validate_signup_session(
        client,
        signup_token=signup_token,
    )

    assert session_response.status_code == 200

    session_data = session_response.json()

    # =====================================================
    # IMPORTANT ASSERTION
    # =====================================================

    assert (
        session_data["type"]
        == "complete_local_setup"
    )

    # =====================================================
    # Step 7 — Complete Local Setup
    # =====================================================

    complete_response = complete_signup(
        client,
        signup_token=signup_token,
        username=username,
        password=password,
        role=UserRole.ARTIST.value,
    )

    assert complete_response.status_code == 200

    complete_data = complete_response.json()

    assert (
        complete_data["message"]
        == "Signup completed successfully"
    )

    # =====================================================
    # Step 8 — User Updated
    # =====================================================

    updated_user = session.exec(
        select(User).where(
            User.email == email,
        ),
    ).first()

    assert updated_user is not None

    # =====================================================
    # IMPORTANT ASSERTIONS
    # =====================================================

    assert (
        updated_user.username
        == username
    )

    # Role SHOULD NOT change.
    # Existing OAuth role preserved.

    assert (
        updated_user.role
        == UserRole.LISTENER.value
    )

    # Password should now exist.

    assert (
        updated_user.password_hash
        is not None
    )

    # =====================================================
    # Step 9 — Local Provider Created
    # =====================================================

    local_provider = session.exec(
        select(AuthProvider).where(
            AuthProvider.user_id
            == updated_user.id,
            AuthProvider.provider
            == AuthProviderType.LOCAL.value,
        ),
    ).first()

    assert local_provider is not None

    # =====================================================
    # Step 10 — Google Provider Still Exists
    # =====================================================

    existing_google_provider = session.exec(
        select(AuthProvider).where(
            AuthProvider.user_id
            == updated_user.id,
            AuthProvider.provider
            == AuthProviderType.GOOGLE.value,
        ),
    ).first()

    assert existing_google_provider is not None

    # =====================================================
    # Step 11 — Pending Signup Cleanup
    # =====================================================

    pending_signup = session.exec(
        select(PendingSignup).where(
            PendingSignup.email == email,
        ),
    ).first()

    assert pending_signup is None

    # =====================================================
    # Step 12 — Refresh Works
    # =====================================================

    refresh_response = refresh_auth_session(
        client,
    )

    assert refresh_response.status_code == 200

    # =====================================================
    # Step 13 — Logout
    # =====================================================

    logout_response = logout(
        client,
    )

    assert logout_response.status_code == 200

    # =====================================================
    # Step 14 — Local Password Login
    # =====================================================

    local_login_response = login(
        client,
        identifier=email,
        password=password,
    )

    if local_login_response.status_code != 200:
        print(local_login_response.json())

    assert (
        local_login_response.status_code
        == 200
    )

    local_login_data = (
        local_login_response.json()
    )

    assert (
        local_login_data["user"]["email"]
        == email
    )

    # =====================================================
    # Step 15 — Refresh Works Again
    # =====================================================

    second_refresh = refresh_auth_session(
        client,
    )

    assert second_refresh.status_code == 200

    # =====================================================
    # Step 16 — Logout Again
    # =====================================================

    second_logout = logout(
        client,
    )

    assert second_logout.status_code == 200

    # =====================================================
    # Step 17 — Google Login Still Works
    # =====================================================

    google_login_response = google_login(
        client,
    )

    assert google_login_response.status_code in (
        200,
        302,
    )

    callback_response = google_callback(
        client,
    )

    assert callback_response.status_code == 302

    redirect_url = callback_response.headers[
        "location"
    ]

    # =====================================================
    # Existing OAuth Login
    # =====================================================

    assert "/oauth/success" in redirect_url

    assert "/oauth/onboarding" not in redirect_url

    # =====================================================
    # Step 18 — Refresh Works Again
    # =====================================================

    final_refresh = refresh_auth_session(
        client,
    )

    assert final_refresh.status_code == 200

    final_refresh_data = (
        final_refresh.json()
    )

    assert (
        final_refresh_data["user"]["email"]
        == email
    )

    # =====================================================
    # Step 19 — Final Logout
    # =====================================================

    final_logout = logout(
        client,
    )

    assert final_logout.status_code == 200