import uuid
from uuid import UUID
from typing import Any
from fastapi import Response
from datetime import datetime, timezone

from sqlmodel import (
    Session, select
)

from app.core.config import settings

from app.models.auth.refresh_session import (
    RefreshSession,
)

from app.services.auth.auth_tokens import (
    create_access_token,
    create_refresh_token,
)

from app.services.auth.password_service import (
    hash_password,
)
from app.services.auth.auth_utils import (
    generate_profile_initial,
)


def create_refresh_session(
    user_id: UUID,
):

    session_id = uuid.uuid4()

    (
        refresh_token,
        refresh_expiration,
    ) = create_refresh_token(
        str(user_id),
        str(session_id),
    )

    refresh_session = RefreshSession(
        id=session_id,
        user_id=user_id,
        token_hash=hash_password(refresh_token),
        expires_at=(refresh_expiration),
    )

    return (
        refresh_token,
        refresh_session,
    )


def get_refresh_session_by_id(
    session: Session,
    session_id: UUID,
) -> RefreshSession | None:

    statement = (
        select(RefreshSession)
        .where(RefreshSession.id == session_id)
        .with_for_update()
    )

    return session.exec(statement).first()


def set_refresh_cookie(
    response: Response,
    refresh_token: str,
):

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        # TODO:
        # Enable secure=True in production
        # after HTTPS deployment.
        secure=False,
        samesite="lax",
        path="/",
        max_age=(settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60),
    )


def clear_refresh_cookie(
    response: Response,
):

    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )


def create_user_auth_session(
    session: Session,
    user,
):

    user.last_login_at = datetime.now(
        timezone.utc,
    )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "token_version": user.token_version,
        }
    )

    (
        refresh_token,
        refresh_session,
    ) = create_refresh_session(
        user.id,
    )

    session.add(
        refresh_session,
    )

    session.commit()

    return (
        access_token,
        refresh_token,
    )
    
def create_access_token_only(user):
    return create_access_token(
        {
            "sub": str(user.id),
            "token_version": user.token_version,
        }
    )


def build_auth_response(
    user,
    access_token: str | None = None,
    message: str | None = None,
):

    response: dict[str, Any] = {
        "user": {
            "id": str(user.id),
            "name": user.name,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_admin": user.is_admin,
            "is_guest": user.is_guest,
            "profile_color": user.profile_color,
            "profile_initial": generate_profile_initial(user.name),
            "created_at": user.created_at,
        },
    }

    if message:
        response["message"] = message

    if access_token:

        response["access_token"] = access_token

        response["token_type"] = "bearer"

    return response
