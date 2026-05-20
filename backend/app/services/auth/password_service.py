from passlib.context import CryptContext
import secrets

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


COMMON_WEAK_PASSWORDS = {
    "password",
    "password123",
    "12345678",
    "qwerty123",
    "admin123",
}


def validate_password_strength(
    password: str,
) -> bool:

    if len(password) < 8:
        return False

    if password.lower() in (COMMON_WEAK_PASSWORDS):
        return False

    return True

def generate_unusable_password_hash() -> str:
    random_password = secrets.token_urlsafe(32)
    return hash_password(random_password)