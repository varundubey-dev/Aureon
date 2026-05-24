from uuid import UUID

from app.utils.datetime import (
    get_utc_now,
)

from fastapi import status

from sqlmodel import Session

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
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)

from app.services.auth.password_service import (
    hash_password,
    verify_password,
)

from app.utils.datetime import (
    ensure_utc_datetime,
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
            "INVALID_CREDENTIALS",
        )

    local_provider = get_local_auth_provider(
        session,
        user.id,
    )

    # OAuth-only account

    if not local_provider:

        raise AuthError(
            status.HTTP_403_FORBIDDEN,
            "This account uses social login. Please continue with Google.",
            "SOCIAL_LOGIN_REQUIRED",
        )

    if not user.password_hash:

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Password login unavailable",
            "PASSWORD_LOGIN_UNAVAILABLE",
        )

    if not verify_password(
        password,
        user.password_hash,
    ):

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid credentials",
            "INVALID_CREDENTIALS",
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
            "REFRESH_TOKEN_MISSING",
        )

    payload = verify_refresh_token(
        refresh_token,
    )

    if not payload:

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid refresh token",
            "INVALID_REFRESH_TOKEN",
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
            "INVALID_REFRESH_TOKEN",
        )

    refresh_session = get_refresh_session_by_id(
        session,
        UUID(session_id),
    )

    if not refresh_session:

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Refresh session invalid",
            "INVALID_REFRESH_SESSION",
        )

    if not verify_password(
        refresh_token,
        refresh_session.token_hash,
    ):

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Refresh session invalid",
            "INVALID_REFRESH_SESSION",
        )

    if str(refresh_session.user_id) != user_id:

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Refresh session invalid",
            "INVALID_REFRESH_SESSION",
        )

    user = session.get(
        User,
        UUID(user_id),
    )

    if not user:

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "User not found",
            "USER_NOT_FOUND",
        )

    expires_at = ensure_utc_datetime(
        refresh_session.expires_at,
    )

    if expires_at < get_utc_now():

        session.delete(
            refresh_session,
        )

        session.commit()

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Refresh token expired",
            "REFRESH_TOKEN_EXPIRED",
        )

    # Sliding refresh session

    now = get_utc_now()

    remaining_time = (expires_at - now).days

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
