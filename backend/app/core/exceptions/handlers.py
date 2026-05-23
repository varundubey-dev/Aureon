from fastapi import Request
from fastapi.responses import JSONResponse

from slowapi.errors import (
    RateLimitExceeded,
)

from app.core.exceptions.base import AppError


async def app_exception_handler(
    request: Request,
    exc: Exception,
):

    if not isinstance(exc, AppError):

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "code": "INTERNAL_SERVER_ERROR",
            },
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": exc.code,
        },
    )


async def rate_limit_exception_handler(
    request: Request,
    exc: Exception,
):

    if not isinstance(exc, RateLimitExceeded):

        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "code": "INTERNAL_SERVER_ERROR",
            },
        )

    return JSONResponse(
        status_code=429,
        content={
            "detail": "Too many requests",
            "code": "RATE_LIMIT_EXCEEDED",
        },
    )
