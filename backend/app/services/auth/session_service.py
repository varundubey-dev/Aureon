import uuid
from uuid import UUID
from typing import Any
from fastapi import Response

from sqlmodel import (
    Session,
)

from app.core.config import settings

from app.models.auth.refresh_session import (
    RefreshSession,
)

from app.services.auth.jwt_service import (
    create_refresh_token,
)

from app.services.auth.password_service import (
    hash_password,
)
from app.services.auth.auth_service import (
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


def get_refresh_session_by_id(
    session: Session,
    session_id: UUID,
) -> RefreshSession | None:

    return session.get(
        RefreshSession,
        session_id,
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
            "profile_color": (user.profile_color),
            "profile_initial": (generate_profile_initial(user.name)),
        },
    }

    if message:
        response["message"] = message

    if access_token:

        response["access_token"] = access_token

        response["token_type"] = "bearer"

    return response
