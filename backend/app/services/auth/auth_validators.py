import re

from fastapi import status

from app.core.enums import (
    UserRole,
)

from app.core.exceptions.auth import (
    AuthError,
)

EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def normalize_email(
    email: str,
) -> str:

    normalized = email.strip().lower()

    if len(normalized) > 254:

        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Invalid email format",
            "INVALID_EMAIL_FORMAT",
        )

    if not EMAIL_REGEX.fullmatch(normalized):

        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Invalid email format",
            "INVALID_EMAIL_FORMAT",
        )

    return normalized


def normalize_username(
    username: str,
) -> str:

    return username.strip().lower()


def trim_name(
    name: str,
) -> str:

    return name.strip()


# TODO:
# Name validation is intentionally simple for MVP.
# Add profanity filtering, unicode normalization,
# and advanced validation rules later.


def validate_name(
    name: str,
) -> bool:

    if len(name) < 2:
        return False

    if len(name) > 50:
        return False

    return True


def validate_username(
    username: str,
) -> bool:

    if len(username) < 3:
        return False

    if len(username) > 30:
        return False

    return username.replace(
        "_",
        "",
    ).isalnum()


def validate_public_role(
    role: str,
) -> bool:

    allowed_roles = {
        UserRole.LISTENER.value,
        UserRole.ARTIST.value,
    }

    return role in allowed_roles
