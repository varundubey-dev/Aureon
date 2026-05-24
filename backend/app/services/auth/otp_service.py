import random

from datetime import (
    datetime,
    timedelta,
)

from passlib.context import (
    CryptContext,
)

from app.models.auth.otp import OTP

from app.core.config import settings

from app.utils.datetime import (
    ensure_utc_datetime,
    get_utc_now,
)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def generate_otp() -> str:

    # Generates 6-digit numeric OTP
    return f"{random.randint(100000, 999999)}"


def hash_otp(
    otp: str,
) -> str:

    return pwd_context.hash(otp)


def verify_otp(
    plain_otp: str,
    hashed_otp: str,
) -> bool:

    return pwd_context.verify(
        plain_otp,
        hashed_otp,
    )


def create_otp_expiration() -> datetime:

    return get_utc_now() + timedelta(
        minutes=(settings.OTP_EXPIRATION_MINUTES)
    )


def is_otp_expired(
    expires_at: datetime,
) -> bool:

    expires_at = ensure_utc_datetime(
        expires_at,
    )

    return get_utc_now() > expires_at


def is_resend_allowed(
    created_at: datetime,
) -> bool:

    created_at = ensure_utc_datetime(
        created_at,
    )

    cooldown = timedelta(seconds=(settings.OTP_RESEND_COOLDOWN_SECONDS))

    return (get_utc_now() - created_at) >= cooldown


def has_exceeded_attempts(
    attempts: int,
) -> bool:

    return attempts >= settings.OTP_MAX_ATTEMPTS


def reset_otp_record(
    otp_record: OTP,
    hashed_otp: str,
    otp_expiration: datetime,
):

    otp_record.otp_hash = hashed_otp
    otp_record.expires_at = otp_expiration
    otp_record.created_at = get_utc_now()
    otp_record.attempts = 0
    otp_record.verified = False