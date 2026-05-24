# =========================================================
# Existing Local User Google OAuth Linking E2E Tests
# =========================================================
#
# This file tests:
#
# Existing local account
# → Google OAuth signup/login
# → automatic provider linking
# → no onboarding flow
#
# Covered areas:
#
# 1. Existing local account detection
# 2. Automatic Google provider linking
# 3. Direct OAuth login flow
# 4. Refresh lifecycle
# 5. Logout lifecycle
# 6. Existing provider login behavior
#
# IMPORTANT:
#
# Existing local users should NOT:
# - receive onboarding flow
# - receive OAuth role selection
# - receive oauth_signup_token
#
# Instead:
# - Google provider gets linked
# - User gets logged in immediately
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

from app.models.auth.refresh_session import (
    RefreshSession,
)

from tests.e2e.helpers.auth_oauth_handlers import (
    google_login,
    google_callback,
)

from app.models.auth.user import (
    User,
)

from app.services.auth.password_service import (
    hash_password,
)

from tests.e2e.helpers.auth_session_handlers import (
    logout,
    refresh_auth_session,
)

# =========================================================
# Existing Local Account OAuth Linking Flow
# =========================================================


def test_existing_local_user_google_oauth_linking_flow(
    client,
    session,
    mock_google_oauth,
):
    """
    Existing local account
    → Google OAuth account linking
    → direct login flow.
    """

    email = mock_google_oauth["email"]

    google_user_id = mock_google_oauth["sub"]

    # =====================================================
    # Step 1 — Create Existing Local User
    # =====================================================

    user = User(
        name="Varun",
        username="varunmusic",
        username_normalized="varunmusic",
        email=email,
        password_hash=hash_password(
            "StrongPass123!",
        ),
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
    )

    session.add(
        user,
    )

    session.commit()

    session.refresh(
        user,
    )

    # =====================================================
    # Step 2 — Existing Local Provider
    # =====================================================

    local_provider = AuthProvider(
        user_id=user.id,
        provider=AuthProviderType.LOCAL.value,
        provider_user_id=email,
    )

    session.add(
        local_provider,
    )

    session.commit()

    # =====================================================
    # Step 3 — Google Login Start
    # =====================================================

    login_response = google_login(
        client,
    )

    assert login_response.status_code in (
        200,
        302,
    )

    # =====================================================
    # Step 4 — Google Callback
    # =====================================================

    callback_response = google_callback(
        client,
    )

    assert callback_response.status_code == 302

    redirect_url = callback_response.headers["location"]

    # =====================================================
    # IMPORTANT ASSERTION
    # =====================================================
    #
    # Existing local users should directly login.
    # NO onboarding flow.
    #
    # =====================================================

    assert "/oauth/success" in redirect_url

    assert "/oauth/onboarding" not in redirect_url

    # =====================================================
    # Step 5 — Google Provider Linked
    # =====================================================

    google_provider = session.exec(
        select(AuthProvider).where(
            AuthProvider.provider == AuthProviderType.GOOGLE.value,
        ),
    ).first()

    assert google_provider is not None

    assert google_provider.user_id == user.id

    assert google_provider.provider_user_id == google_user_id

    # =====================================================
    # Step 6 — Refresh Cookie Created
    # =====================================================

    set_cookie_header = callback_response.headers.get(
        "set-cookie",
        "",
    )

    assert "refresh_token=" in set_cookie_header

    # =====================================================
    # Step 7 — Refresh Session Created
    # =====================================================

    refresh_session = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
        ),
    ).first()

    assert refresh_session is not None

    # =====================================================
    # Step 8 — Refresh Works
    # =====================================================

    refresh_response = refresh_auth_session(
        client,
    )

    assert refresh_response.status_code == 200

    refresh_data = refresh_response.json()

    assert refresh_data["user"]["email"] == email

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

    failed_refresh = refresh_auth_session(
        client,
    )

    assert failed_refresh.status_code in (
        401,
        403,
    )

    # =====================================================
    # Step 11 — Login Again Using Google
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

    # =====================================================
    # Existing OAuth Login
    # =====================================================

    assert "/oauth/success" in second_redirect_url

    assert "/oauth/onboarding" not in second_redirect_url

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

    second_refresh = refresh_auth_session(
        client,
    )

    assert second_refresh.status_code == 200

    second_refresh_data = second_refresh.json()

    assert second_refresh_data["user"]["email"] == email

    # =====================================================
    # Step 14 — Final Logout
    # =====================================================

    final_logout = logout(
        client,
    )

    assert final_logout.status_code == 200
