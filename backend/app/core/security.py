from fastapi import Response

REFRESH_COOKIE_NAME = "refresh_token"


def set_refresh_cookie(
    response: Response,
    refresh_token: str,
) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=False,  # True in prod
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/",
    )


def clear_refresh_cookie(
    response: Response,
) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/",
    )


# TODO:
# Restrict cookie path to auth refresh routes in production.
# Using "/" temporarily during early development.
# path="/",
