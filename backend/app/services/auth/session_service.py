from uuid import UUID

from fastapi import Response

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


def create_refresh_session(
    user_id: UUID,
):

    (
        refresh_token,
        refresh_expiration,
    ) = create_refresh_token(
        {
            "sub": str(user_id),
        }
    )

    refresh_session = RefreshSession(
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
        max_age=(settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60),
    )


def build_auth_response(
    user,
    access_token: str,
):

    return {
        "message": ("Signup completed successfully"),
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "name": user.name,
            "username": (user.username),
            "email": user.email,
            "role": user.role,
            "profile_color": (user.profile_color),
        },
    }
