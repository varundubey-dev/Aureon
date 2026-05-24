# =========================================================
# Refresh Session Cleanup Tests
# =========================================================
#
# This file tests:
#
# cleanup_expired_refresh_sessions()
#
# Covered areas:
#
# 1. Expired refresh session cleanup
#    - Expired session deletion
#
# 2. Active refresh session protection
#    - Non-expired session preservation
#
# 3. Guest cleanup behavior
#    - Guest deletion when all sessions expire
#    - Guest preservation when active sessions remain
#
# 4. Regular user protection
#    - Non-guest users never deleted
#
# 5. Cleanup statistics
#    - Correct deleted session count
#    - Correct deleted guest count
#
# NOTE:
#
# - Scheduler behavior is NOT tested here.
# - This file tests ONLY cleanup logic.
#
# =========================================================

from datetime import timedelta

from sqlmodel import (
    select,
)

from app.core.enums import (
    UserRole,
)

from app.models.auth.refresh_session import (
    RefreshSession,
)

from app.models.auth.user import (
    User,
)

from app.services.auth.auth_sessions import (
    create_refresh_session,
)

from app.services.maintenance.session_cleanup import (
    cleanup_expired_refresh_sessions,
)

from app.utils.datetime import (
    get_utc_now,
)

# =========================================================
# Helpers
# =========================================================


def create_guest_user(
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
        token_version=0,
    )

    session.add(user)
    session.commit()

    return user


def create_regular_user(
    session,
):

    user = User(
        name="Regular User",
        username="regular",
        username_normalized="regular",
        email="regular@example.com",
        password_hash="hashed",
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=False,
        profile_color="#ffffff",
        token_version=0,
    )

    session.add(user)
    session.commit()

    return user


def create_session(
    session,
    *,
    user_id,
    expired=True,
):

    (
        refresh_token,
        refresh_session,
    ) = create_refresh_session(
        user_id,
    )

    refresh_session.expires_at = (
        get_utc_now() - timedelta(days=1)
        if expired
        else get_utc_now() + timedelta(days=30)
    )

    session.add(
        refresh_session,
    )

    session.commit()

    return refresh_session


# =========================================================
# Refresh Session Cleanup
# =========================================================


def test_cleanup_deletes_expired_refresh_session(
    session,
):

    user = create_regular_user(
        session,
    )

    refresh_session = create_session(
        session,
        user_id=user.id,
        expired=True,
    )

    result = cleanup_expired_refresh_sessions(
        session,
    )

    deleted_session = session.get(
        RefreshSession,
        refresh_session.id,
    )

    assert result["deleted_sessions"] == 1

    assert result["deleted_guests"] == 0

    assert deleted_session is None


def test_cleanup_preserves_active_refresh_session(
    session,
):

    user = create_regular_user(
        session,
    )

    refresh_session = create_session(
        session,
        user_id=user.id,
        expired=False,
    )

    result = cleanup_expired_refresh_sessions(
        session,
    )

    existing_session = session.get(
        RefreshSession,
        refresh_session.id,
    )

    assert result["deleted_sessions"] == 0

    assert result["deleted_guests"] == 0

    assert existing_session is not None


def test_cleanup_deletes_guest_when_no_active_sessions_remain(
    session,
):

    guest = create_guest_user(
        session,
    )

    refresh_session = create_session(
        session,
        user_id=guest.id,
        expired=True,
    )

    result = cleanup_expired_refresh_sessions(
        session,
    )

    deleted_guest = session.get(
        User,
        guest.id,
    )

    deleted_session = session.get(
        RefreshSession,
        refresh_session.id,
    )

    assert result["deleted_sessions"] == 1

    assert result["deleted_guests"] == 1

    assert deleted_guest is None

    assert deleted_session is None


def test_cleanup_preserves_guest_with_active_sessions(
    session,
):

    guest = create_guest_user(
        session,
    )

    expired_session = create_session(
        session,
        user_id=guest.id,
        expired=True,
    )

    active_session = create_session(
        session,
        user_id=guest.id,
        expired=False,
    )

    result = cleanup_expired_refresh_sessions(
        session,
    )

    existing_guest = session.get(
        User,
        guest.id,
    )

    remaining_session = session.get(
        RefreshSession,
        active_session.id,
    )

    deleted_session = session.get(
        RefreshSession,
        expired_session.id,
    )

    assert result["deleted_sessions"] == 1

    assert result["deleted_guests"] == 0

    assert existing_guest is not None

    assert remaining_session is not None

    assert deleted_session is None


def test_cleanup_never_deletes_regular_user(
    session,
):

    user = create_regular_user(
        session,
    )

    create_session(
        session,
        user_id=user.id,
        expired=True,
    )

    result = cleanup_expired_refresh_sessions(
        session,
    )

    existing_user = session.get(
        User,
        user.id,
    )

    assert result["deleted_sessions"] == 1

    assert result["deleted_guests"] == 0

    assert existing_user is not None


def test_cleanup_handles_multiple_expired_sessions(
    session,
):

    guest = create_guest_user(
        session,
    )

    regular_user = create_regular_user(
        session,
    )

    create_session(
        session,
        user_id=guest.id,
        expired=True,
    )

    create_session(
        session,
        user_id=regular_user.id,
        expired=True,
    )

    result = cleanup_expired_refresh_sessions(
        session,
    )

    remaining_sessions = session.exec(
        select(RefreshSession),
    ).all()

    deleted_guest = session.get(
        User,
        guest.id,
    )

    existing_regular_user = session.get(
        User,
        regular_user.id,
    )

    assert result["deleted_sessions"] == 2

    assert result["deleted_guests"] == 1

    assert len(remaining_sessions) == 0

    assert deleted_guest is None

    assert existing_regular_user is not None
