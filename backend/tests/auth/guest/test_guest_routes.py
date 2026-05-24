# =========================================================
# Guest Route Tests
# =========================================================
#
# This file tests:
#
# POST /api/v1/auth/guest
#
# Covered areas:
#
# 1. Guest account creation
#    - Guest user persistence
#    - Refresh session creation
#    - Refresh cookie setting
#    - Access token response
#
# NOTE:
#
# - Guest business logic itself is tested separately.
# - This file focuses ONLY on route integration behavior.
#
# =========================================================

from sqlmodel import select

from app.models.auth.refresh_session import (
    RefreshSession,
)

from app.models.auth.user import (
    User,
)

# =========================================================
# Guest Account Creation
# =========================================================


def test_create_guest_account_success(
    client,
    session,
):

    response = client.post(
        "/api/v1/auth/guest",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Guest account created"

    assert "access_token" in data

    user_id = data["user"]["id"]

    created_user = session.get(
        User,
        user_id,
    )

    assert created_user is not None

    assert created_user.is_guest is True

    assert created_user.email is None

    assert created_user.username is None

    refresh_session = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == created_user.id,
        )
    ).first()

    assert refresh_session is not None

    cookies = response.cookies

    assert "refresh_token" in cookies
