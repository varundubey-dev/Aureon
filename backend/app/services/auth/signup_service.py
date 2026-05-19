import random
from sqlmodel import Session, select

from app.core.enums import OTPPurpose, UserRole

from app.models.auth.user import User
from app.models.auth.pending_signup import (
    PendingSignup,
)
from app.models.auth.otp import OTP


def normalize_email(
    email: str,
) -> str:
    return email.strip().lower()


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


def is_email_taken(
    session: Session,
    email: str,
) -> bool:

    normalized_email = normalize_email(
        email
    )

    existing_user = session.exec(
        select(User).where(
            User.email == normalized_email
        )
    ).first()

    return existing_user is not None


def get_pending_signup(
    session: Session,
    email: str,
) -> PendingSignup | None:

    normalized_email = normalize_email(
        email
    )

    return session.exec(
        select(PendingSignup).where(
            PendingSignup.email == normalized_email
        )
    ).first()


def get_signup_otp(
    session: Session,
    email: str,
) -> OTP | None:

    normalized_email = normalize_email(
        email
    )

    return session.exec(
        select(OTP).where(
            OTP.email == normalized_email,
            OTP.purpose == OTPPurpose.SIGNUP.value,
        )
    ).first()


def has_active_signup_state(
    session: Session,
    email: str,
) -> bool:

    pending_signup = get_pending_signup(
        session,
        email,
    )

    return pending_signup is not None

def normalize_username(
    username: str,
) -> str:
    return username.strip().lower()


def validate_username(
    username: str,
) -> bool:

    if len(username) < 3:
        return False

    if len(username) > 30:
        return False

    return username.replace(
        "_",
        ""
    ).isalnum()


def is_username_taken(
    session: Session,
    username: str,
) -> bool:

    normalized_username = (
        normalize_username(
            username
        )
    )

    existing_user = session.exec(
        select(User).where(
            User.username_normalized
            == normalized_username
        )
    ).first()

    return existing_user is not None


def validate_public_role(
    role: str,
) -> bool:

    allowed_roles = {
        UserRole.LISTENER.value,
        UserRole.ARTIST.value,
    }

    return role in allowed_roles

PROFILE_COLORS = [
    "#FF6B6B",
    "#4ECDC4",
    "#45B7D1",
    "#FFA94D",
    "#A78BFA",
]


def generate_profile_initial(
    name: str,
) -> str:
    return name[0].upper()


def generate_profile_color() -> str:
    import random

    return random.choice(
        PROFILE_COLORS
    )

def generate_username_suggestions(
    session: Session,
    name: str,
) -> list[str]:

    base_username = (
        normalize_username(
            name.replace(
                " ",
                ""
            )
        )
    )

    suggestions = []

    if not is_username_taken(
        session,
        base_username,
    ):
        suggestions.append(
            base_username
        )

    while len(suggestions) < 5:

        random_number = random.randint(
            100,
            9999,
        )

        candidate = (
            f"{base_username}"
            f"{random_number}"
        )

        if (
            candidate
            not in suggestions
            and not is_username_taken(
                session,
                candidate,
            )
        ):
            suggestions.append(
                candidate
            )

    return suggestions