from sqlmodel import (
    Session,
    select,
)

from app.core.enums import OTPPurpose

from app.models.auth.user import User
from app.models.auth.pending_signup import PendingSignup
from app.models.auth.otp import OTP

from app.services.auth.auth_validators import (
    normalize_email,
    normalize_username,
)


def get_pending_signup(
    session: Session,
    email: str,
) -> PendingSignup | None:

    normalized_email = normalize_email(email)

    return session.exec(
        select(PendingSignup).where(
            PendingSignup.email == normalized_email,
        )
    ).first()


def get_signup_otp(
    session: Session,
    email: str,
) -> OTP | None:

    normalized_email = normalize_email(email)

    return session.exec(
        select(OTP).where(
            OTP.email == normalized_email,
            OTP.purpose == OTPPurpose.SIGNUP.value,
        )
    ).first()


def get_user_by_email(
    session: Session,
    email: str,
) -> User | None:

    normalized_email = normalize_email(email)

    return session.exec(
        select(User).where(
            User.email == normalized_email,
        )
    ).first()


def get_user_by_username(
    session: Session,
    username: str,
) -> User | None:

    normalized_username = normalize_username(username)

    return session.exec(
        select(User).where(
            User.username_normalized == normalized_username,
        )
    ).first()


def get_user_by_identifier(
    session: Session,
    identifier: str,
) -> User | None:

    if "@" in identifier:

        return get_user_by_email(
            session,
            identifier,
        )

    return get_user_by_username(
        session,
        identifier,
    )


def is_email_taken(
    session: Session,
    email: str,
) -> bool:

    return (
        get_user_by_email(
            session,
            email,
        )
        is not None
    )


def is_username_taken(
    session: Session,
    username: str,
) -> bool:

    return (
        get_user_by_username(
            session,
            username,
        )
        is not None
    )