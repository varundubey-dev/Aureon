from datetime import datetime, timedelta, timezone, timedelta
from typing import Any

from jose import jwt, JWTError

from app.core.config import settings


def create_access_token(
    data: dict[str, Any],
) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire,
        "type": "access",
    })

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    data: dict[str, Any],
) -> tuple[str, datetime]:

    to_encode = data.copy()

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    )

    to_encode.update({
        "exp": expire,
        "type": "refresh",
    })

    token = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    return token, expire


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )

def create_signup_token(
    email: str,
) -> str:

    expiration = datetime.now(
        timezone.utc
    ) + timedelta(
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
            algorithms=[
                settings.JWT_ALGORITHM
            ],
        )

        token_type = payload.get(
            "type"
        )

        if token_type != "signup":
            return None

        email = payload.get(
            "sub"
        )

        if not email:
            return None

        return email

    except JWTError:
        return None