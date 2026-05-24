# =========================================================
# Password Reset E2E Flow Tests
# =========================================================
#
# Flow:
#
# Existing local user
# → Password reset request
# → OTP verification
# → Password reset completion
# → Old password fails
# → New password login works
# → Refresh works
# → Logout works
#
# Covered areas:
#
# 1. Password reset request
# 2. OTP generation
# 3. OTP verification
# 4. Reset token generation
# 5. Password replacement
# 6. Old credential invalidation
# 7. New credential authentication
# 8. Refresh session invalidation
# 9. Refresh lifecycle
#
# IMPORTANT:
#
# Password reset should:
# - invalidate old password
# - revoke old refresh sessions
# - increment token version
# - delete OTP after completion
#
# =========================================================

from sqlmodel import select

from app.core.enums import (
    AuthProviderType,
    OTPPurpose,
    UserRole,
)

from app.models.auth.auth_provider import (
    AuthProvider,
)

from app.models.auth.otp import (
    OTP,
)

from app.models.auth.refresh_session import (
    RefreshSession,
)

from app.models.auth.user import (
    User,
)

from app.services.auth.password_service import (
    hash_password,
)

from tests.e2e.helpers.auth_login_handlers import (
    login,
)

from tests.e2e.helpers.auth_session_handlers import (
    logout,
    refresh_auth_session,
)

from tests.e2e.helpers.auth_password_reset_handlers import(
     request_password_reset,
     verify_password_reset_otp,
     complete_password_reset
)

from tests.e2e.utils.otp_utils import (
    extract_otp,
)

# =========================================================
# Full Password Reset Flow
# =========================================================


def test_password_reset_complete_flow(
    client,
    session,
    mock_send_email,
):
    """
    Complete password reset lifecycle.
    """

    email = "varun@example.com"

    old_password = "OldPass123!"

    new_password = "NewPass123!"

    # =====================================================
    # Step 1 — Create Existing Local User
    # =====================================================

    user = User(
        name="Varun",
        username="varunmusic",
        username_normalized="varunmusic",
        email=email,
        password_hash=hash_password(
            old_password,
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
    # Step 2 — Create Local Provider
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
    # Step 3 — Initial Login
    # =====================================================

    initial_login = login(
        client,
        identifier=email,
        password=old_password,
    )

    assert initial_login.status_code == 200

    # =====================================================
    # Step 4 — Refresh Session Exists
    # =====================================================

    refresh_session = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
        ),
    ).first()

    assert refresh_session is not None

    # =====================================================
    # Step 5 — Request Password Reset
    # =====================================================

    reset_request = request_password_reset(
        client,
        email=email,
    )

    assert reset_request.status_code == 200

    reset_request_data = reset_request.json()

    assert reset_request_data["type"] == "otp_sent"

    # =====================================================
    # Step 6 — OTP Email Sent
    # =====================================================

    assert mock_send_email["password_reset"].call_count == 1

    sent_email = mock_send_email["password_reset"].call_args_list[0].kwargs

    assert sent_email["recipient"] == email

    assert sent_email["subject"] == "Aureon Password Reset OTP"

    otp = extract_otp(
        sent_email["body"],
    )

    # =====================================================
    # Step 7 — OTP Record Created
    # =====================================================

    otp_record = session.exec(
        select(OTP).where(
            OTP.email == email,
            OTP.purpose == OTPPurpose.PASSWORD_RESET.value,
        ),
    ).first()

    assert otp_record is not None

    # =====================================================
    # Step 8 — Verify OTP
    # =====================================================

    verify_response = verify_password_reset_otp(
        client,
        email=email,
        otp=otp,
    )

    assert verify_response.status_code == 200

    verify_data = verify_response.json()

    assert verify_data["type"] == "otp_verified"

    reset_token = verify_data["reset_token"]

    assert reset_token is not None

    # =====================================================
    # Step 9 — Complete Password Reset
    # =====================================================

    complete_response = complete_password_reset(
        client,
        reset_token=reset_token,
        new_password=new_password,
    )

    assert complete_response.status_code == 200

    complete_data = complete_response.json()

    assert complete_data["type"] == "password_reset_completed"

    # =====================================================
    # Step 10 — Refresh Sessions Revoked
    # =====================================================

    revoked_sessions = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
        ),
    ).all()

    assert len(revoked_sessions) == 0

    # =====================================================
    # Step 11 — OTP Cleanup
    # =====================================================

    deleted_otp = session.exec(
        select(OTP).where(
            OTP.email == email,
            OTP.purpose == OTPPurpose.PASSWORD_RESET.value,
        ),
    ).first()

    assert deleted_otp is None

    # =====================================================
    # Step 12 — Old Password Should Fail
    # =====================================================

    old_login = login(
        client,
        identifier=email,
        password=old_password,
    )

    assert old_login.status_code in (
        400,
        401,
    )

    # =====================================================
    # Step 13 — New Password Login Works
    # =====================================================

    new_login = login(
        client,
        identifier=email,
        password=new_password,
    )

    if new_login.status_code != 200:
        print(new_login.json())

    assert new_login.status_code == 200

    new_login_data = new_login.json()

    assert new_login_data["user"]["email"] == email

    # =====================================================
    # Step 14 — Refresh Works
    # =====================================================

    refresh_response = refresh_auth_session(
        client,
    )

    assert refresh_response.status_code == 200

    refresh_data = refresh_response.json()

    assert refresh_data["user"]["email"] == email

    # =====================================================
    # Step 15 — Logout Works
    # =====================================================

    logout_response = logout(
        client,
    )

    assert logout_response.status_code == 200

    # =====================================================
    # Step 16 — Refresh Fails After Logout
    # =====================================================

    failed_refresh = refresh_auth_session(
        client,
    )

    assert failed_refresh.status_code in (
        401,
        403,
    )
