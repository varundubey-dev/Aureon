from sqlmodel import (
    Session,
    select,
)

from app.core.enums import OTPPurpose

from app.models.auth.user import User
from app.models.auth.pending_signup import PendingSignup
from app.models.auth.otp import OTP
from app.models.auth.auth_provider import AuthProvider
from app.core.enums import AuthProviderType

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


def get_auth_provider(
    session: Session,
    provider: str,
    provider_user_id: str,
) -> AuthProvider | None:

    return session.exec(
        select(AuthProvider).where(
            AuthProvider.provider == provider,
            AuthProvider.provider_user_id == provider_user_id,
        )
    ).first()


def get_user_by_provider(
    session: Session,
    provider: str,
    provider_user_id: str,
) -> User | None:

    auth_provider = get_auth_provider(
        session,
        provider,
        provider_user_id,
    )

    if not auth_provider:
        return None

    return session.get(
        User,
        auth_provider.user_id,
    )


def get_local_auth_provider(
    session: Session,
    user_id,
) -> AuthProvider | None:

    return session.exec(
        select(AuthProvider).where(
            AuthProvider.user_id == user_id,
            AuthProvider.provider == AuthProviderType.LOCAL.value,
        )
    ).first()


def create_auth_provider(
    session: Session,
    *,
    user_id,
    provider: str,
    provider_user_id: str,
):

    auth_provider = AuthProvider(
        user_id=user_id,
        provider=provider,
        provider_user_id=provider_user_id,
    )

    session.add(auth_provider)

    return auth_provider


def get_auth_provider_by_user(
    session: Session,
    user_id,
    provider: str,
) -> AuthProvider | None:

    return session.exec(
        select(AuthProvider).where(
            AuthProvider.user_id == user_id,
            AuthProvider.provider == provider,
        )
    ).first()


def has_auth_provider(
    session: Session,
    user_id,
    provider: str,
) -> bool:

    return (
        get_auth_provider_by_user(
            session,
            user_id,
            provider,
        )
        is not None
    )


def has_local_auth_provider(
    session: Session,
    user_id,
) -> bool:

    return has_auth_provider(
        session,
        user_id,
        AuthProviderType.LOCAL.value,
    )


def has_google_auth_provider(
    session: Session,
    user_id,
) -> bool:

    return has_auth_provider(
        session,
        user_id,
        AuthProviderType.GOOGLE.value,
    )
