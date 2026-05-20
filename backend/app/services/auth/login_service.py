from datetime import (
    datetime,
    timezone,
)

from uuid import UUID

from fastapi import status

from sqlmodel import Session

from app.models.auth.user import User

from app.services.auth.auth_queries import (
    get_user_by_identifier,
)

from app.services.auth.password_service import (
    verify_password,
)

from app.services.auth.auth_tokens import (
    create_access_token,
    verify_refresh_token,
)

from app.services.auth.auth_sessions import (
    create_refresh_session,
    get_refresh_session_by_id,
)

from app.core.exceptions.auth import AuthError


def handle_login(
    session: Session,
    identifier: str,
    password: str,
):

    user = get_user_by_identifier(
        session,
        identifier,
    )

    if not user:
        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid credentials",
        )

    if not user.password_hash:
        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid credentials",
        )

    if not verify_password(
        password,
        user.password_hash,
    ):
        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid credentials",
        )

    user.last_login_at = datetime.now(timezone.utc)

    session.add(user)

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "token_version": user.token_version,
        }
    )

    (
        refresh_token,
        refresh_session,
    ) = create_refresh_session(user.id)

    session.add(refresh_session)

    session.commit()

    return (
        user,
        access_token,
        refresh_token,
    )


def handle_refresh_token(
    session: Session,
    refresh_token: str | None,
):

    if not refresh_token:
        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Refresh token missing",
        )

    payload = verify_refresh_token(
        refresh_token,
    )

    if not payload:
        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid refresh token",
        )

    user_id = payload.get("sub")
    session_id = payload.get("jti")

    if not user_id or not session_id:
        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid refresh token",
        )

    user_id = UUID(user_id)
    session_id = UUID(session_id)

    refresh_session = get_refresh_session_by_id(
        session,
        session_id,
    )

    if not refresh_session:
        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Refresh session invalid",
        )

    if not verify_password(
        refresh_token,
        refresh_session.token_hash,
    ):
        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Refresh session invalid",
        )

    if refresh_session.user_id != user_id:
        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Refresh session invalid",
        )

    user = session.get(
        User,
        user_id,
    )

    if not user:
        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "User not found",
        )

    if refresh_session.expires_at < datetime.now(timezone.utc):

        session.delete(refresh_session)

        session.commit()

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Refresh token expired",
        )

    # token rotation
    session.delete(refresh_session)

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "token_version": user.token_version,
        }
    )

    (
        new_refresh_token,
        new_refresh_session,
    ) = create_refresh_session(user.id)

    session.add(new_refresh_session)

    session.commit()

    return (
        access_token,
        new_refresh_token,
    )


def handle_logout(
    session: Session,
    refresh_token: str | None,
):

    if not refresh_token:
        return

    payload = verify_refresh_token(
        refresh_token,
    )

    if not payload:
        return

    session_id = payload.get("jti")

    if not session_id:
        return

    refresh_session = get_refresh_session_by_id(
        session,
        UUID(session_id),
    )

    if not refresh_session:
        return

    session.delete(refresh_session)

    session.commit()