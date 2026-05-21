from datetime import (
    datetime,
    timezone,
)

from fastapi import status

from sqlmodel import (
    Session,
)

from app.core.enums import (
    AuthProviderType,
    OTPPurpose,
    UserRole,
)

from app.core.exceptions.auth import (
    AuthError,
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

from app.services.auth.auth_queries import (
    create_auth_provider,
    get_pending_signup,
    get_signup_otp,
    get_user_by_email,
    has_local_auth_provider,
    is_username_taken,
)

from app.services.auth.auth_sessions import (
    create_user_auth_session,
)

from app.services.auth.auth_tokens import (
    create_signup_token,
    verify_signup_token,
)

from app.services.auth.auth_utils import (
    generate_profile_color,
    generate_username_suggestions,
)

from app.services.auth.auth_validators import (
    normalize_email,
    normalize_username,
    trim_name,
    validate_name,
    validate_public_role,
    validate_username,
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

LOCAL_PROVIDER = AuthProviderType.LOCAL.value


def handle_signup_request(
    session: Session,
    email: str,
    name: str,
    existing_user_id=None,
):

    normalized_email = normalize_email(
        email,
    )

    trimmed_name = trim_name(
        name,
    )

    if not validate_name(
        trimmed_name,
    ):

        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Invalid name format",
        )

    existing_user = get_user_by_email(
        session,
        normalized_email,
    )

    # ==========================================
    # Existing Account
    # ==========================================

    if existing_user:

        if not existing_user.email:

            raise AuthError(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Account email corrupted",
            )

        # ==========================================
        # Existing Local Account
        # ==========================================

        if has_local_auth_provider(
            session,
            existing_user.id,
        ):

            raise AuthError(
                status.HTTP_400_BAD_REQUEST,
                "Account already exists",
            )

        # ==========================================
        # OAuth-only Account
        # ==========================================

        signup_token = create_signup_token(
            existing_user.email,
        )

        return {
            "type": "complete_local_setup",
            "signup_token": signup_token,
            "email": existing_user.email,
            "name": existing_user.name,
        }

    existing_pending_signup = get_pending_signup(
        session,
        normalized_email,
    )

    existing_otp = get_signup_otp(
        session,
        normalized_email,
    )

    if existing_pending_signup and existing_pending_signup.verified:

        signup_token = create_signup_token(
            normalized_email,
        )

        username_suggestions = generate_username_suggestions(
            session,
            existing_pending_signup.name,
        )

        return {
            "type": "resume_signup",
            "signup_token": signup_token,
            "email": normalized_email,
            "name": existing_pending_signup.name,
            "username_suggestions": username_suggestions,
        }

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

    hashed_otp = hash_otp(
        otp,
    )

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

    session.add(
        otp_record,
    )

    session.add(
        pending_signup,
    )

    email_body = generate_otp_email_template(
        otp,
    )

    session.commit()

    return {
        "type": "otp_verification",
        "message": "OTP sent successfully",
        "email_data": {
            "recipient": normalized_email,
            "subject": "Aureon Signup OTP",
            "body": email_body,
        },
    }


def handle_verify_signup_otp(
    session: Session,
    email: str,
    otp: str,
):

    normalized_email = normalize_email(
        email,
    )

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
            ("Pending signup state corrupted"),
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
            ("Maximum OTP attempts exceeded"),
        )

    if not verify_otp(
        otp,
        otp_record.otp_hash,
    ):

        otp_record.attempts += 1

        session.add(
            otp_record,
        )

        session.commit()

        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Invalid OTP",
        )

    otp_record.verified = True

    pending_signup.verified = True

    session.add(
        otp_record,
    )

    session.add(
        pending_signup,
    )

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
        "username_suggestions": (username_suggestions),
    }


def handle_resend_signup_otp(
    session: Session,
    email: str,
):

    normalized_email = normalize_email(
        email,
    )

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
            ("Pending signup not found"),
        )

    if pending_signup.verified:

        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            ("Signup already verified"),
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
            ("OTP resend cooldown active"),
        )

    otp = generate_otp()

    hashed_otp = hash_otp(
        otp,
    )

    otp_expiration = create_otp_expiration()

    reset_otp_record(
        otp_record,
        hashed_otp,
        otp_expiration,
    )

    pending_signup.otp_hash = hashed_otp
    pending_signup.otp_expires_at = otp_expiration
    pending_signup.verified = False

    session.add(
        otp_record,
    )

    session.add(
        pending_signup,
    )

    email_body = generate_otp_email_template(
        otp,
    )

    session.commit()

    return {
        "email_data": {
            "recipient": normalized_email,
            "subject": "Aureon Signup OTP",
            "body": email_body,
        },
    }


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

    password_hash = hash_password(
        password,
    )

    # ==========================================
    # Existing OAuth-only Account
    # ==========================================

    existing_user = get_user_by_email(
        session,
        signup_email,
    )

    if existing_user:

        if has_local_auth_provider(
            session,
            existing_user.id,
        ):

            raise AuthError(
                status.HTTP_400_BAD_REQUEST,
                "Local login already configured",
            )

        user = existing_user
        user.username = username
        user.username_normalized = normalized_username
        user.password_hash = password_hash

        session.add(
            user,
        )

        create_auth_provider(
            session,
            user_id=user.id,
            provider=LOCAL_PROVIDER,
            provider_user_id=signup_email,
        )

        (
            access_token,
            refresh_token,
        ) = create_user_auth_session(
            session,
            user,
        )

        session.commit()

        return (
            user,
            access_token,
            refresh_token,
        )

    # ==========================================
    # Normal Signup Flow
    # ==========================================

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

    if not validate_public_role(
        role,
    ):

        raise AuthError(
            status.HTTP_403_FORBIDDEN,
            "Invalid public role",
        )

    # ==========================================
    # Guest Upgrade
    # ==========================================

    if pending_signup.existing_user_id:

        if role != UserRole.LISTENER.value:

            raise AuthError(
                status.HTTP_403_FORBIDDEN,
                ("Guest accounts can only " "upgrade to listener accounts"),
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
            normalized_username=(normalized_username),
            email=pending_signup.email,
            password_hash=password_hash,
        )

    # ==========================================
    # Fresh Local Signup
    # ==========================================

    else:

        user = User(
            name=pending_signup.name,
            username=username,
            username_normalized=(normalized_username),
            email=pending_signup.email,
            password_hash=password_hash,
            role=role,
            is_admin=False,
            is_guest=False,
            profile_color=(generate_profile_color()),
            last_login_at=datetime.now(
                timezone.utc,
            ),
        )

        session.add(
            user,
        )

        session.flush()

    if not has_local_auth_provider(
        session,
        user.id,
    ):

        create_auth_provider(
            session,
            user_id=user.id,
            provider=LOCAL_PROVIDER,
            provider_user_id=signup_email,
        )

    (
        access_token,
        refresh_token,
    ) = create_user_auth_session(
        session,
        user,
    )

    otp_record = get_signup_otp(
        session,
        signup_email,
    )

    if otp_record:

        session.delete(
            otp_record,
        )

    session.delete(
        pending_signup,
    )

    session.commit()

    return (
        user,
        access_token,
        refresh_token,
    )
