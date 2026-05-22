from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.auth.refresh_session import RefreshSession
from app.models.auth.user import User


def cleanup_expired_refresh_sessions(
    session: Session,
):

    now = datetime.now(
        timezone.utc,
    )

    expired_sessions = session.exec(
        select(RefreshSession).where(
            RefreshSession.expires_at < now,
        ),
    ).all()

    deleted_count = 0

    deleted_guest_count = 0

    for refresh_session in expired_sessions:

        user = session.get(
            User,
            refresh_session.user_id,
        )

        session.delete(
            refresh_session,
        )

        deleted_count += 1

        # Delete guest if no active sessions remain
        if user and user.is_guest:

            active_sessions = session.exec(
                select(RefreshSession).where(
                    RefreshSession.user_id == user.id,
                    RefreshSession.expires_at > now,
                ),
            ).all()

            if not active_sessions:

                session.delete(
                    user,
                )

                deleted_guest_count += 1

    session.commit()

    return {
        "deleted_sessions": deleted_count,
        "deleted_guests": deleted_guest_count,
    }
