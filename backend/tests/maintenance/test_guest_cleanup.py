# =========================================================
# Guest Cleanup Tests
# =========================================================
#
# This file tests:
#
# cleanup_inactive_guest_accounts()
#
# Covered areas:
#
# 1. Expired inactive guest cleanup
#    - Old guest deletion
#
# 2. Active guest protection
#    - Guest with refresh session preserved
#
# 3. Non-guest protection
#    - Regular users never deleted
#
# 4. Recent guest protection
#    - Recently active guest preserved
#
# 5. Cleanup count tracking
#    - Correct deletion count returned
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

from app.models.auth.user import (
    User,
)

from app.services.auth.auth_sessions import (
    create_refresh_session,
)

from app.services.maintenance.guest_cleanup import (
    cleanup_inactive_guest_accounts,
)

from app.utils.datetime import (
    get_utc_now,
)

# =========================================================
# Helpers
# =========================================================


def create_guest_user(
    session,
    *,
    days_old=10,
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
        last_login_at=get_utc_now() - timedelta(days=days_old),
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
        last_login_at=get_utc_now() - timedelta(days=30),
    )

    session.add(user)
    session.commit()

    return user


# =========================================================
# Guest Cleanup
# =========================================================


def test_cleanup_deletes_inactive_guest_without_sessions(
    session,
):

    guest = create_guest_user(
        session,
        days_old=10,
    )

    deleted_count = cleanup_inactive_guest_accounts(
        session,
    )

    deleted_guest = session.get(
        User,
        guest.id,
    )

    assert deleted_count == 1

    assert deleted_guest is None


def test_cleanup_preserves_guest_with_active_session(
    session,
):

    guest = create_guest_user(
        session,
        days_old=10,
    )

    (
        refresh_token,
        refresh_session,
    ) = create_refresh_session(
        guest.id,
    )

    session.add(
        refresh_session,
    )

    session.commit()

    deleted_count = cleanup_inactive_guest_accounts(
        session,
    )

    existing_guest = session.get(
        User,
        guest.id,
    )

    assert deleted_count == 0

    assert existing_guest is not None


def test_cleanup_preserves_recent_guest(
    session,
):

    guest = create_guest_user(
        session,
        days_old=2,
    )

    deleted_count = cleanup_inactive_guest_accounts(
        session,
    )

    existing_guest = session.get(
        User,
        guest.id,
    )

    assert deleted_count == 0

    assert existing_guest is not None


def test_cleanup_never_deletes_regular_users(
    session,
):

    user = create_regular_user(
        session,
    )

    deleted_count = cleanup_inactive_guest_accounts(
        session,
    )

    existing_user = session.get(
        User,
        user.id,
    )

    assert deleted_count == 0

    assert existing_user is not None


def test_cleanup_deletes_only_eligible_guests(
    session,
):

    deletable_guest = create_guest_user(
        session,
        days_old=15,
    )

    protected_guest = create_guest_user(
        session,
        days_old=15,
    )

    (
        refresh_token,
        refresh_session,
    ) = create_refresh_session(
        protected_guest.id,
    )

    session.add(
        refresh_session,
    )

    recent_guest = create_guest_user(
        session,
        days_old=1,
    )

    regular_user = create_regular_user(
        session,
    )

    session.commit()

    deleted_count = cleanup_inactive_guest_accounts(
        session,
    )

    remaining_users = session.exec(
        select(User),
    ).all()

    remaining_ids = {
        user.id for user in remaining_users
    }

    assert deleted_count == 1

    assert deletable_guest.id not in remaining_ids

    assert protected_guest.id in remaining_ids

    assert recent_guest.id in remaining_ids

    assert regular_user.id in remaining_ids