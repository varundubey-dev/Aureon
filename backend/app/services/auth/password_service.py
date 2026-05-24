from passlib.context import CryptContext
import secrets

from app.core.constants.auth import (
    COMMON_WEAK_PASSWORDS,
    PASSWORD_REGEX,
)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:

    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


def validate_password_strength(
    password: str,
) -> bool:

    if password.lower() in COMMON_WEAK_PASSWORDS:
        return False

    return bool(
        PASSWORD_REGEX.fullmatch(
            password,
        )
    )


def generate_unusable_password_hash() -> str:

    random_password = secrets.token_urlsafe(32)

    return hash_password(
        random_password,
    )
