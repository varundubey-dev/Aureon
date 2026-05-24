from datetime import datetime, timedelta
from typing import Any
from app.utils.datetime import (
    get_utc_now,
)

from jose import jwt, JWTError

from app.core.config import settings


def create_access_token(
    data: dict[str, Any],
) -> str:
    to_encode = data.copy()

    expire = get_utc_now() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update(
        {
            "exp": expire,
            "type": "access",
        }
    )

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_access_token(
    token: str,
) -> dict | None:

    try:

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if payload.get("type") != "access":
            return None

        return payload

    except JWTError:
        return None


def create_refresh_token(
    user_id: str,
    session_id: str,
) -> tuple[str, datetime]:

    expire = get_utc_now() + timedelta(
        days=(settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    payload = {
        "sub": user_id,
        "jti": session_id,
        "exp": expire,
        "type": "refresh",
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=(settings.JWT_ALGORITHM),
    )

    return (
        token,
        expire,
    )


def verify_refresh_token(
    token: str,
) -> dict | None:

    try:

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if payload.get("type") != "refresh":
            return None

        return payload

    except JWTError:
        return None


def create_signup_token(
    email: str,
) -> str:

    expiration = get_utc_now() + timedelta(
        minutes=settings.SIGNUP_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": email,
        "type": "signup",
        "exp": expiration,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_signup_token(
    token: str,
) -> str | None:

    try:

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        token_type = payload.get("type")

        if token_type != "signup":
            return None

        email = payload.get("sub")

        if not email:
            return None

        return email

    except JWTError:
        return None

def create_password_reset_token(
    email: str,
) -> str:

    expiration = (
        get_utc_now()
        + timedelta(minutes=15)
    )

    payload = {
        "sub": email,
        "type": "password_reset",
        "exp": expiration,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_password_reset_token(
    token: str,
) -> str | None:

    try:

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[
                settings.JWT_ALGORITHM
            ],
        )

        if (
            payload.get("type")
            != "password_reset"
        ):
            return None

        email = payload.get("sub")

        if not email:
            return None

        return email

    except JWTError:
        return None

def create_oauth_signup_token(
    data: dict[str, Any],
) -> str:

    expiration = get_utc_now() + timedelta(minutes=15)

    payload = {
        **data,
        "type": "oauth_signup",
        "exp": expiration,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

def verify_oauth_signup_token(
    token: str,
) -> dict | None:

    try:

        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[
                settings.JWT_ALGORITHM,
            ],
        )

        if (
            payload.get("type")
            != "oauth_signup"
        ):
            return None

        return payload

    except JWTError:
        return None