from fastapi import Response
from app.core.config import settings

REFRESH_COOKIE_NAME = "refresh_token"


def set_refresh_cookie(
    response: Response,
    refresh_token: str,
):
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        # TODO:
        # Enable secure=True in production
        # after HTTPS deployment.
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/",
        max_age=(settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60),
    )


def clear_refresh_cookie(
    response: Response,
):

    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


# TODO:
# Restrict cookie path to auth refresh routes in production.
# Using "/" temporarily during early development.
# path="/",
