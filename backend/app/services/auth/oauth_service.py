from sqlmodel import (
    Session,
)

from app.core.enums import (
    AuthProviderType,
)

from app.core.exceptions.auth import (
    AuthError,
)

from app.models.auth.user import (
    User,
)

from app.services.auth.auth_queries import (
    create_auth_provider,
    get_user_by_email,
    get_user_by_provider,
)

from app.services.auth.auth_sessions import (
    create_user_auth_session,
)

from app.services.auth.auth_tokens import (
    create_oauth_signup_token,
    verify_oauth_signup_token,
)

from app.services.auth.auth_utils import (
    generate_available_username,
    generate_profile_color
)

from app.services.auth.auth_validators import (
    validate_public_role,
)

from app.services.auth.guest_service import (
    upgrade_guest_account,
)

from app.services.auth.password_service import (
    generate_unusable_password_hash,
)

GOOGLE_PROVIDER = AuthProviderType.GOOGLE.value

def build_oauth_user(
    session: Session,
    *,
    name: str,
    email: str,
    role: str,
) -> User:

    (
        username,
        normalized_username,
    ) = generate_available_username(
        session,
        name,
    )

    user = User(
        name=name,
        username=username,
        username_normalized=normalized_username,
        email=email,
        password_hash=generate_unusable_password_hash(),
        role=role,
        is_admin=False,
        is_guest=False,
        profile_color=generate_profile_color(),
    )

    session.add(
        user,
    )

    session.flush()

    return user


def handle_google_auth_callback(
    session: Session,
    *,
    google_user_id: str | None,
    email: str | None,
    name: str | None,
    current_user: User | None = None,
):

    if not google_user_id or not email or not name:

        raise AuthError(
            400,
            "Invalid Google user data",
        )

    # ==========================================
    # Existing Google OAuth Login
    # ==========================================

    provider_user = get_user_by_provider(
        session,
        GOOGLE_PROVIDER,
        google_user_id,
    )

    if provider_user:

        (
            access_token,
            refresh_token,
        ) = create_user_auth_session(
            session,
            provider_user,
        )

        return {
            "type": "login",
            "user": provider_user,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    # ==========================================
    # Guest Upgrade Flow
    # ==========================================

    if current_user and current_user.is_guest:

        (
            username,
            normalized_username,
        ) = generate_available_username(
            session,
            name,
        )

        user = upgrade_guest_account(
            session,
            current_user,
            name=name,
            username=username,
            normalized_username=normalized_username,
            email=email,
            password_hash=(generate_unusable_password_hash()),
        )

        create_auth_provider(
            session,
            user_id=user.id,
            provider=GOOGLE_PROVIDER,
            provider_user_id=google_user_id,
        )

        (
            access_token,
            refresh_token,
        ) = create_user_auth_session(
            session,
            user,
        )

        return {
            "type": "login",
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    # ==========================================
    # Existing User Account Linking
    # ==========================================

    existing_user = get_user_by_email(
        session,
        email,
    )

    if existing_user:

        create_auth_provider(
            session,
            user_id=existing_user.id,
            provider=GOOGLE_PROVIDER,
            provider_user_id=google_user_id,
        )

        (
            access_token,
            refresh_token,
        ) = create_user_auth_session(
            session,
            existing_user,
        )

        return {
            "type": "login",
            "user": existing_user,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    # ==========================================
    # New OAuth Signup
    # ==========================================

    oauth_signup_token = create_oauth_signup_token(
        {
            "sub": email,
            "name": name,
            "google_user_id": google_user_id,
        }
    )

    return {
        "type": "onboarding",
        "oauth_signup_token": (oauth_signup_token),
        "email": email,
        "name": name,
    }


def handle_complete_oauth_signup(
    session: Session,
    *,
    oauth_signup_token: str,
    role: str,
):

    payload = verify_oauth_signup_token(
        oauth_signup_token,
    )

    if not payload:

        raise AuthError(
            401,
            ("Invalid or expired OAuth signup token"),
        )

    if not validate_public_role(
        role,
    ):

        raise AuthError(
            403,
            "Invalid public role",
        )

    email = payload.get(
        "sub",
    )

    name = payload.get(
        "name",
    )

    google_user_id = payload.get(
        "google_user_id",
    )

    if not email or not name or not google_user_id:

        raise AuthError(
            400,
            ("Invalid OAuth signup payload"),
        )

    existing_user = get_user_by_email(
        session,
        email,
    )

    if existing_user:

        raise AuthError(
            409,
            "Account already exists",
        )

    user = build_oauth_user(
        session,
        name=name,
        email=email,
        role=role,
    )

    create_auth_provider(
        session,
        user_id=user.id,
        provider=GOOGLE_PROVIDER,
        provider_user_id=google_user_id,
    )

    (
        access_token,
        refresh_token,
    ) = create_user_auth_session(
        session,
        user,
    )

    return (
        user,
        access_token,
        refresh_token,
    )
