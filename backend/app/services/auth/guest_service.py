from datetime import (
    datetime,
    timezone,
)

from sqlmodel import (
    Session,
    select,
)

from app.core.enums import UserRole

from app.models.auth.user import User
from app.models.auth.refresh_session import RefreshSession

from app.services.auth.auth_utils import generate_profile_color


def is_guest_user(
    user: User,
) -> bool:

    return user.is_guest


def create_guest_user() -> User:

    return User(
        name="Guest",
        username=None,
        username_normalized=None,
        email=None,
        password_hash=None,
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=True,
        profile_color=generate_profile_color(),
        token_version=0,
        created_at=datetime.now(timezone.utc),
        last_login_at=datetime.now(timezone.utc),
    )


def revoke_user_refresh_sessions(
    session: Session,
    user_id,
) -> None:

    refresh_sessions = session.exec(
        select(RefreshSession).where(RefreshSession.user_id == user_id)
    ).all()

    for refresh_session in refresh_sessions:
        session.delete(refresh_session)


def invalidate_user_tokens(
    user: User,
) -> None:

    user.token_version += 1


def upgrade_guest_account(
    session: Session,
    user: User,
    *,
    name: str,
    username: str,
    normalized_username: str,
    email: str,
    password_hash: str,
) -> User:

    user.name = name
    user.username = username
    user.username_normalized = normalized_username
    user.email = email
    user.password_hash = password_hash
    user.role = UserRole.LISTENER.value
    user.is_guest = False
    user.last_login_at = datetime.now(timezone.utc)

    invalidate_user_tokens(user)

    revoke_user_refresh_sessions(
        session,
        user.id,
    )

    return user
