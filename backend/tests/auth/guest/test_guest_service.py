# =========================================================
# Guest Service Tests
# =========================================================
#
# This file tests:
#
# 1. Guest user creation
#    - Default guest values
#    - Listener role assignment
#    - Token version initialization
#    - Empty auth fields
#
# 2. Guest detection
#    - is_guest_user()
#
# 3. Token invalidation
#    - token_version incrementing
#
# 4. Refresh session revocation
#    - User refresh session cleanup
#    - Targeted deletion behavior
#
# 5. Guest account upgrade
#    - Account field updates
#    - Guest removal
#    - Token invalidation
#    - Refresh session cleanup
#    - Listener role enforcement
#
# NOTE:
#
# - This file tests ONLY guest-domain logic.
# - Signup endpoint integration is tested separately.
#
# =========================================================

from sqlmodel import select

from app.core.enums import UserRole

from app.models.auth.refresh_session import RefreshSession
from app.models.auth.user import User

from app.services.auth.auth_sessions import (
    create_refresh_session,
)

from app.services.auth.guest_service import (
    create_guest_user,
    invalidate_user_tokens,
    is_guest_user,
    revoke_user_refresh_sessions,
    upgrade_guest_account,
)

# =========================================================
# Guest Creation
# =========================================================


def test_create_guest_user_defaults():

    guest_user = create_guest_user()

    assert guest_user.name == "Guest"

    assert guest_user.username is None
    assert guest_user.username_normalized is None

    assert guest_user.email is None
    assert guest_user.password_hash is None

    assert guest_user.role == UserRole.LISTENER.value

    assert guest_user.is_admin is False
    assert guest_user.is_guest is True

    assert guest_user.token_version == 0

    assert guest_user.profile_color is not None

    assert guest_user.created_at is not None
    assert guest_user.last_login_at is not None


# =========================================================
# Guest Detection
# =========================================================


def test_is_guest_user_true():

    user = User(
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

    assert is_guest_user(user) is True


def test_is_guest_user_false():

    user = User(
        name="Varun",
        username="varun",
        username_normalized="varun",
        email="varun@example.com",
        password_hash="hashed",
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
    )

    assert is_guest_user(user) is False


# =========================================================
# Token Invalidation
# =========================================================


def test_invalidate_user_tokens():

    user = User(
        name="Guest",
        username=None,
        username_normalized=None,
        email=None,
        password_hash=None,
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=True,
        profile_color="#ffffff",
        token_version=2,
    )

    invalidate_user_tokens(
        user,
    )

    assert user.token_version == 3


# =========================================================
# Refresh Session Revocation
# =========================================================


def test_revoke_user_refresh_sessions(
    session,
):

    user = User(
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

    other_user = User(
        name="Other",
        username="other",
        username_normalized="other",
        email="other@example.com",
        password_hash="hashed",
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
    )

    session.add(user)
    session.add(other_user)

    session.flush()

    refresh_token_1, refresh_session_1 = create_refresh_session(
        user.id,
    )

    refresh_token_2, refresh_session_2 = create_refresh_session(
        user.id,
    )

    refresh_token_3, refresh_session_3 = create_refresh_session(
        other_user.id,
    )

    session.add(refresh_session_1)
    session.add(refresh_session_2)
    session.add(refresh_session_3)

    session.commit()

    revoke_user_refresh_sessions(
        session,
        user.id,
    )

    session.commit()

    remaining_sessions = session.exec(select(RefreshSession)).all()

    assert len(remaining_sessions) == 1

    assert remaining_sessions[0].user_id == other_user.id


# =========================================================
# Guest Upgrade
# =========================================================


def test_upgrade_guest_account_success(
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
        token_version=0,
    )

    session.add(guest_user)

    session.flush()

    refresh_token, refresh_session = create_refresh_session(
        guest_user.id,
    )

    session.add(
        refresh_session,
    )

    session.commit()

    updated_user = upgrade_guest_account(
        session,
        guest_user,
        name="Varun",
        username="varun",
        normalized_username="varun",
        email="varun@example.com",
        password_hash="hashed_password",
    )

    session.add(
        updated_user,
    )

    session.commit()

    assert updated_user.name == "Varun"

    assert updated_user.username == "varun"
    assert updated_user.username_normalized == "varun"

    assert updated_user.email == "varun@example.com"

    assert updated_user.password_hash == "hashed_password"

    assert updated_user.role == UserRole.LISTENER.value

    assert updated_user.is_guest is False

    assert updated_user.token_version == 1

    assert updated_user.last_login_at is not None

    refresh_sessions = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == updated_user.id,
        )
    ).all()

    assert len(refresh_sessions) == 0
