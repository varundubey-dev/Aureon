from fastapi import status

from app.core.enums import (
    UserRole,
)

from app.core.constants.auth import (
    EMAIL_REGEX,
    NAME_REGEX,
    USERNAME_REGEX,
    USERNAME_MIN_LENGTH,
    USERNAME_MAX_LENGTH,
    NAME_MAX_LENGTH,
    NAME_MIN_LENGTH,
)

from app.core.exceptions.auth import (
    AuthError,
)


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

    trimmed_name = name.strip()

    if len(trimmed_name) < NAME_MIN_LENGTH:
        return False

    if len(trimmed_name) > NAME_MAX_LENGTH:
        return False

    return bool(
        NAME_REGEX.fullmatch(
            trimmed_name,
        )
    )


def validate_username(
    username: str,
) -> bool:

    if len(username) < USERNAME_MIN_LENGTH:
        return False

    if len(username) > USERNAME_MAX_LENGTH:
        return False

    if (
        username.startswith("_")
        or username.endswith("_")
        or username.startswith(".")
        or username.endswith(".")
    ):
        return False

    return bool(
        USERNAME_REGEX.fullmatch(
            username,
        )
    )


def validate_public_role(
    role: str,
) -> bool:

    allowed_roles = {
        UserRole.LISTENER.value,
        UserRole.ARTIST.value,
    }

    return role in allowed_roles
