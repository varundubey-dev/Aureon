from datetime import (
    datetime,
    timezone,
)

from fastapi import status

from sqlmodel import (
    Session,
    select,
)

from app.core.enums import (
    AuthProviderType,
    OTPPurpose,
    UserRole,
)

from app.core.exceptions.auth import (
    AuthError,
)

from app.models.auth.auth_provider import (
    AuthProvider,
)

from app.models.auth.otp import (
    OTP,
)

from app.models.auth.pending_signup import (
    PendingSignup,
)

from app.models.auth.user import (
    User,
)

from app.services.auth.auth_utils import (
    generate_profile_color,
    generate_username_suggestions,
)

from app.services.auth.auth_queries import (
    get_pending_signup,
    get_signup_otp,
    is_email_taken,
    is_username_taken,
)

from app.services.auth.auth_sessions import (
    create_refresh_session,
)

from app.services.auth.auth_tokens import (
    create_access_token,
    create_signup_token,
    verify_signup_token,
)

from app.services.auth.auth_validators import (
    normalize_email,
    normalize_username,
    trim_name,
    validate_name,
    validate_public_role,
    validate_username,
)

from app.services.auth.email_service import (
    send_email,
)

from app.services.auth.email_templates import (
    generate_otp_email_template,
)

from app.services.auth.guest_service import (
    upgrade_guest_account,
)

from app.services.auth.otp_service import (
    create_otp_expiration,
    generate_otp,
    hash_otp,
    has_exceeded_attempts,
    is_otp_expired,
    is_resend_allowed,
    reset_otp_record,
    verify_otp,
)

from app.services.auth.password_service import (
    hash_password,
    validate_password_strength,
)


def handle_signup_request(
    session: Session,
    email: str,
    name: str,
    existing_user_id=None,
):

    normalized_email = normalize_email(email)

    trimmed_name = trim_name(name)

    if not validate_name(trimmed_name):
        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Invalid name format",
        )

    if is_email_taken(
        session,
        normalized_email,
    ):
        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Email already exists",
        )

    existing_pending_signup = get_pending_signup(
        session,
        normalized_email,
    )

    existing_otp = get_signup_otp(
        session,
        normalized_email,
    )

    if existing_pending_signup and existing_pending_signup.verified:
        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Signup already verified",
        )

    if existing_otp:
        if not is_otp_expired(
            existing_otp.expires_at,
        ):
            if not is_resend_allowed(
                existing_otp.created_at,
            ):
                raise AuthError(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    "OTP resend cooldown active",
                )

    otp = generate_otp()

    hashed_otp = hash_otp(otp)

    otp_expiration = create_otp_expiration()

    if existing_otp:
        otp_record = existing_otp

        reset_otp_record(
            otp_record,
            hashed_otp,
            otp_expiration,
        )

    else:
        otp_record = OTP(
            email=normalized_email,
            purpose=OTPPurpose.SIGNUP.value,
            otp_hash=hashed_otp,
            expires_at=otp_expiration,
        )

    if existing_pending_signup:
        pending_signup = existing_pending_signup

        pending_signup.name = trimmed_name
        pending_signup.otp_hash = hashed_otp
        pending_signup.otp_expires_at = otp_expiration
        pending_signup.verified = False
        pending_signup.existing_user_id = existing_user_id

    else:
        pending_signup = PendingSignup(
            name=trimmed_name,
            email=normalized_email,
            otp_hash=hashed_otp,
            otp_expires_at=otp_expiration,
            verified=False,
            existing_user_id=existing_user_id,
        )

    session.add(otp_record)
    session.add(pending_signup)

    session.commit()

    email_body = generate_otp_email_template(
        otp,
    )

    email_sent = send_email(
        recipient=normalized_email,
        subject="Aureon Signup OTP",
        body=email_body,
    )

    if not email_sent:
        raise AuthError(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to send OTP email",
        )


def handle_verify_signup_otp(
    session: Session,
    email: str,
    otp: str,
):

    normalized_email = normalize_email(email)

    otp_record = get_signup_otp(
        session,
        normalized_email,
    )

    if not otp_record:
        raise AuthError(
            status.HTTP_404_NOT_FOUND,
            "OTP not found",
        )

    pending_signup = get_pending_signup(
        session,
        normalized_email,
    )

    if not pending_signup:
        raise AuthError(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Pending signup state corrupted",
        )

    if pending_signup.verified:
        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Signup already verified",
        )

    if otp_record.verified:
        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "OTP already verified",
        )

    if is_otp_expired(
        otp_record.expires_at,
    ):
        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "OTP expired",
        )

    if has_exceeded_attempts(
        otp_record.attempts,
    ):
        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Maximum OTP attempts exceeded",
        )

    if not verify_otp(
        otp,
        otp_record.otp_hash,
    ):
        otp_record.attempts += 1

        session.add(otp_record)

        session.commit()

        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Invalid OTP",
        )

    otp_record.verified = True
    pending_signup.verified = True

    session.add(otp_record)
    session.add(pending_signup)

    session.commit()

    signup_token = create_signup_token(
        normalized_email,
    )

    username_suggestions = generate_username_suggestions(
        session,
        pending_signup.name,
    )

    return {
        "signup_token": signup_token,
        "username_suggestions": username_suggestions,
    }


def handle_resend_signup_otp(
    session: Session,
    email: str,
):

    normalized_email = normalize_email(email)

    otp_record = get_signup_otp(
        session,
        normalized_email,
    )

    if not otp_record:
        raise AuthError(
            status.HTTP_404_NOT_FOUND,
            "OTP not found",
        )

    pending_signup = get_pending_signup(
        session,
        normalized_email,
    )

    if not pending_signup:
        raise AuthError(
            status.HTTP_404_NOT_FOUND,
            "Pending signup not found",
        )

    if pending_signup.verified:
        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Signup already verified",
        )

    if otp_record.verified:
        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "OTP already verified",
        )

    if not is_resend_allowed(
        otp_record.created_at,
    ):
        raise AuthError(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "OTP resend cooldown active",
        )

    otp = generate_otp()

    hashed_otp = hash_otp(otp)

    otp_expiration = create_otp_expiration()

    reset_otp_record(
        otp_record,
        hashed_otp,
        otp_expiration,
    )

    pending_signup.otp_hash = hashed_otp
    pending_signup.otp_expires_at = otp_expiration
    pending_signup.verified = False

    session.add(otp_record)
    session.add(pending_signup)

    session.commit()

    email_body = generate_otp_email_template(
        otp,
    )

    email_sent = send_email(
        recipient=normalized_email,
        subject="Aureon Signup OTP",
        body=email_body,
    )

    if not email_sent:
        raise AuthError(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to resend OTP email",
        )


def handle_complete_signup(
    session: Session,
    *,
    signup_token: str,
    username: str,
    password: str,
    confirm_password: str,
    role: str,
):

    signup_email = verify_signup_token(
        signup_token,
    )

    if not signup_email:
        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or expired signup token",
        )

    pending_signup = get_pending_signup(
        session,
        signup_email,
    )

    if not pending_signup:
        raise AuthError(
            status.HTTP_404_NOT_FOUND,
            "Pending signup not found",
        )

    if not pending_signup.verified:
        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            "Signup verification required",
        )

    normalized_username = normalize_username(
        username,
    )

    if not validate_username(
        normalized_username,
    ):
        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Invalid username format",
        )

    if is_username_taken(
        session,
        normalized_username,
    ):
        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Username already taken",
        )

    if password != confirm_password:
        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Passwords do not match",
        )

    if not validate_password_strength(
        password,
    ):
        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Weak password",
        )

    if not validate_public_role(
        role,
    ):
        raise AuthError(
            status.HTTP_403_FORBIDDEN,
            "Invalid public role",
        )

    password_hash = hash_password(
        password,
    )

    if pending_signup.existing_user_id:
        if role != UserRole.LISTENER.value:
            raise AuthError(
                status.HTTP_403_FORBIDDEN,
                "Guest accounts can only upgrade to listener accounts",
            )

        user = session.get(
            User,
            pending_signup.existing_user_id,
        )

        if not user:
            raise AuthError(
                status.HTTP_404_NOT_FOUND,
                "Existing user not found",
            )

        user = upgrade_guest_account(
            session,
            user,
            name=pending_signup.name,
            username=username,
            normalized_username=normalized_username,
            email=pending_signup.email,
            password_hash=password_hash,
        )

    else:
        user = User(
            name=pending_signup.name,
            username=username,
            username_normalized=normalized_username,
            email=pending_signup.email,
            password_hash=password_hash,
            role=role,
            is_admin=False,
            is_guest=False,
            profile_color=generate_profile_color(),
            last_login_at=datetime.now(timezone.utc),
        )

        session.add(user)

        session.flush()

    existing_provider = session.exec(
        select(AuthProvider).where(
            AuthProvider.user_id == user.id,
            AuthProvider.provider == AuthProviderType.LOCAL.value,
        )
    ).first()

    if not existing_provider:
        auth_provider = AuthProvider(
            user_id=user.id,
            provider=AuthProviderType.LOCAL.value,
            provider_user_id=signup_email,
        )

        session.add(auth_provider)

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "token_version": user.token_version,
        }
    )

    (
        refresh_token,
        refresh_session,
    ) = create_refresh_session(
        user.id,
    )

    session.add(refresh_session)

    otp_record = get_signup_otp(
        session,
        signup_email,
    )

    if otp_record:
        session.delete(otp_record)

    session.delete(pending_signup)

    session.commit()

    return (
        user,
        access_token,
        refresh_token,
    )
