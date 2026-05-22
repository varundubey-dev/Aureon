from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select, col

from app.models.auth.refresh_session import RefreshSession
from app.models.auth.user import User


def cleanup_inactive_guest_accounts(
    session: Session,
) -> int:

    cutoff = datetime.now(
        timezone.utc,
    ) - timedelta(days=7)

    guest_users = session.exec(
        select(User).where(
            User.is_guest,
            col(User.last_login_at) < cutoff,
        ),
    ).all()

    deleted_count = 0

    for guest in guest_users:

        active_sessions = session.exec(
            select(RefreshSession).where(
                RefreshSession.user_id == guest.id,
            ),
        ).all()

        # Still active somewhere
        if active_sessions:
            continue

        session.delete(
            guest,
        )

        deleted_count += 1

    session.commit()

    return deleted_count