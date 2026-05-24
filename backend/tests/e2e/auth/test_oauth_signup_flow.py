# =========================================================
# Google OAuth Signup E2E Flow Tests
# =========================================================
#
# This file tests:
# /api/v1/auth/google/login
# /api/v1/auth/google/callback
# /api/v1/auth/google/complete
# /api/v1/auth/refresh
# /api/v1/auth/logout
#
# Covered areas:
#
# 1. New OAuth signup flow
#    - Google callback
#    - OAuth onboarding token generation
#    - Role selection
#    - OAuth signup completion
#
# 2. Login/session lifecycle
#    - Existing OAuth login
#    - Refresh flow
#    - Logout flow
#
# 3. Database integrity
#    - User creation
#    - Google provider creation
#    - Refresh session creation
#
# NOTE:
#
# - Google SDK internals are mocked.
# - JWT internals are NOT tested here.
# - OAuth provider validation internals are NOT tested here.
#
# =========================================================
# =========================================================
# Google OAuth Signup E2E Flow Tests
# =========================================================

from urllib.parse import (
    parse_qs,
    urlparse,
)


from sqlmodel import select

from app.core.enums import (
    AuthProviderType,
    UserRole,
)

from app.models.auth.auth_provider import (
    AuthProvider,
)

from app.models.auth.refresh_session import (
    RefreshSession,
)

from app.models.auth.user import (
    User,
)

from tests.e2e.helpers.auth_session_handlers import (
    logout,
    refresh_auth_session,
)

from tests.e2e.helpers.auth_oauth_handlers import (
    google_login,
    google_callback,
    complete_google_signup,
)

# =========================================================
# Full OAuth Flow
# =========================================================


def test_new_google_oauth_signup_login_refresh_logout_flow(
    client,
    session,
    mock_google_oauth,
):

    role = UserRole.LISTENER.value

    email = mock_google_oauth["email"]

    google_user_id = mock_google_oauth["sub"]

    # =====================================================
    # Step 1 — Google Login Start
    # =====================================================

    login_response = google_login(
        client,
    )

    assert login_response.status_code in (
        200,
        302,
    )

    # =====================================================
    # Step 2 — Google Callback
    # =====================================================

    callback_response = google_callback(
        client,
    )

    assert callback_response.status_code == 302

    redirect_url = callback_response.headers["location"]

    assert "/oauth/onboarding" in redirect_url

    # =====================================================
    # Step 3 — Extract OAuth Token
    # =====================================================

    parsed_url = urlparse(
        redirect_url,
    )

    query_params = parse_qs(
        parsed_url.query,
    )

    oauth_signup_token = query_params["token"][0]

    assert oauth_signup_token is not None

    # =====================================================
    # Step 4 — Complete OAuth Signup
    # =====================================================

    complete_response = complete_google_signup(
        client,
        oauth_signup_token=oauth_signup_token,
        role=role,
    )

    assert complete_response.status_code == 200

    complete_data = complete_response.json()

    assert complete_data["message"] == "OAuth signup completed successfully"

    # =====================================================
    # Step 5 — Refresh Cookie Created
    # =====================================================

    set_cookie_header = complete_response.headers.get(
        "set-cookie",
        "",
    )

    assert "refresh_token=" in set_cookie_header

    # =====================================================
    # Step 6 — User Created
    # =====================================================

    user = session.exec(
        select(User).where(
            User.email == email,
        ),
    ).first()

    assert user is not None

    assert user.email == email

    assert user.name == "Varun"

    assert user.role == role

    assert user.username is not None

    # =====================================================
    # Step 7 — Google Provider Created
    # =====================================================

    provider = session.exec(
        select(AuthProvider).where(
            AuthProvider.user_id == user.id,
        ),
    ).first()

    assert provider is not None

    assert provider.provider == AuthProviderType.GOOGLE.value

    assert provider.provider_user_id == google_user_id

    # =====================================================
    # Step 8 — Refresh Session Created
    # =====================================================

    refresh_session = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
        ),
    ).first()

    assert refresh_session is not None

    # =====================================================
    # Step 9 — Logout
    # =====================================================

    logout_response = logout(
        client,
    )

    assert logout_response.status_code == 200

    # =====================================================
    # Step 10 — Refresh Should Fail
    # =====================================================

    refresh_response = refresh_auth_session(
        client,
    )

    assert refresh_response.status_code in (
        401,
        403,
    )

    # =====================================================
    # Step 11 — Existing OAuth Login
    # =====================================================

    second_login_response = google_login(
        client,
    )

    assert second_login_response.status_code in (
        200,
        302,
    )

    second_callback_response = google_callback(
        client,
    )

    assert second_callback_response.status_code == 302

    second_redirect_url = second_callback_response.headers["location"]

    assert "/oauth/success" in second_redirect_url

    # =====================================================
    # Step 12 — Refresh Cookie Exists Again
    # =====================================================

    second_cookie = second_callback_response.headers.get(
        "set-cookie",
        "",
    )

    assert "refresh_token=" in second_cookie

    # =====================================================
    # Step 13 — Refresh Works Again
    # =====================================================

    refresh_response = refresh_auth_session(
        client,
    )

    assert refresh_response.status_code == 200

    refresh_data = refresh_response.json()

    assert refresh_data["user"]["email"] == email

    # =====================================================
    # Step 14 — Final Logout
    # =====================================================

    final_logout_response = logout(
        client,
    )

    assert final_logout_response.status_code == 200
