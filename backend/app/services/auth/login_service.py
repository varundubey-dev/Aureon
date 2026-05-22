from uuid import UUID

from fastapi import status

from sqlmodel import Session

from datetime import (
    datetime,
    timezone,
)

from app.core.exceptions.auth import (
    AuthError,
)

from app.models.auth.user import (
    User,
)

from app.services.auth.auth_queries import (
    get_local_auth_provider,
    get_user_by_identifier,
)

from app.services.auth.auth_sessions import (
    create_user_auth_session,
    get_refresh_session_by_id,
)

from app.services.auth.auth_tokens import (
    verify_refresh_token,
    create_refresh_token,
    create_access_token,
)

from app.services.auth.password_service import (
    verify_password,
    hash_password,
)


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

    local_provider = get_local_auth_provider(
        session,
        user.id,
    )

        # OAuth-only account
    
    if not local_provider:

        raise AuthError(
            status.HTTP_403_FORBIDDEN,
            ("This account uses social login. Please continue with Google."),
        )

    if not user.password_hash:

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Password login unavailable",
        )

    if not verify_password(
        password,
        user.password_hash,
    ):

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid credentials",
        )

    (
        access_token,
        refresh_token,
    ) = create_user_auth_session(
        session,
        user,
    )

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

    user_id = payload.get(
        "sub",
    )

    session_id = payload.get(
        "jti",
    )

    if not user_id or not session_id:

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid refresh token",
        )

    refresh_session = get_refresh_session_by_id(
        session,
        UUID(session_id),
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

    if str(refresh_session.user_id) != user_id:

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Refresh session invalid",
        )

    user = session.get(
        User,
        UUID(user_id),
    )

    if not user:

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "User not found",
        )

    if refresh_session.expires_at < datetime.now(timezone.utc):

        session.delete(
            refresh_session,
        )

        session.commit()

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Refresh token expired",
        )

        # Sliding refresh session
    
    now = datetime.now(timezone.utc)

    remaining_time = (refresh_session.expires_at - now).days

    # Default:
    # Keep SAME refresh token
    new_refresh_token = None

    # Renew ONLY near expiry
    if remaining_time <= 7:

        (
            new_refresh_token,
            new_expiration,
        ) = create_refresh_token(
            str(user.id),
            str(refresh_session.id),
        )

        refresh_session.token_hash = hash_password(
            new_refresh_token,
        )

        refresh_session.expires_at = new_expiration

        session.add(
            refresh_session,
        )

    # New short-lived access token
    access_token = create_access_token(
        {
            "sub": str(user.id),
            "token_version": user.token_version,
        }
    )

    session.commit()

    return (
        user,
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

    session_id = payload.get(
        "jti",
    )

    if not session_id:
        return

    refresh_session = get_refresh_session_by_id(
        session,
        UUID(session_id),
    )

    if not refresh_session:
        return

    session.delete(
        refresh_session,
    )

    session.commit()
