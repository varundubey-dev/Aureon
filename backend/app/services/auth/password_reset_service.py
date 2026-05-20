from fastapi import status

from sqlmodel import (
    Session,
    select,
)

from app.core.enums import (
    OTPPurpose,
)

from app.core.exceptions.auth import (
    AuthError,
)

from app.models.auth.otp import (
    OTP,
)

from app.models.auth.refresh_session import (
    RefreshSession,
)

from app.services.auth.auth_queries import (
    get_local_auth_provider,
    get_user_by_email,
)

from app.services.auth.auth_validators import (
    normalize_email,
)

from app.services.auth.auth_tokens import (
    create_password_reset_token,
    verify_password_reset_token,
)

from app.services.auth.email_service import (
    send_email,
)

from app.services.auth.email_templates import (
    generate_password_reset_email_template,
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


def handle_password_reset_request(
    session: Session,
    email: str,
):

    normalized_email = normalize_email(
        email,
    )

    user = get_user_by_email(
        session,
        normalized_email,
    )

    # ==========================================
    # Silent success:
    # Never reveal account existence
    # ==========================================

    if not user:
        return

    # ==========================================
    # Google-only accounts
    # ==========================================

    local_provider = get_local_auth_provider(
        session,
        user.id,
    )

    if not local_provider:

        raise AuthError(
            status.HTTP_403_FORBIDDEN,
            ("Password reset unavailable for social login accounts"),
        )

    existing_otp = session.exec(
        select(OTP).where(
            OTP.email == normalized_email,
            OTP.purpose == OTPPurpose.PASSWORD_RESET.value,
        )
    ).first()

    if existing_otp:

        if not is_otp_expired(
            existing_otp.expires_at,
        ):

            if not is_resend_allowed(
                existing_otp.created_at,
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
            purpose=(OTPPurpose.PASSWORD_RESET.value),
            otp_hash=hashed_otp,
            expires_at=otp_expiration,
        )

    session.add(
        otp_record,
    )

    session.commit()

    email_body = generate_password_reset_email_template(
        otp,
    )

    send_email(
        recipient=normalized_email,
        subject=("Aureon Password Reset OTP"),
        body=email_body,
    )


def handle_verify_password_reset_otp(
    session: Session,
    email: str,
    otp: str,
):

    normalized_email = normalize_email(
        email,
    )

    otp_record = session.exec(
        select(OTP).where(
            OTP.email == normalized_email,
            OTP.purpose == OTPPurpose.PASSWORD_RESET.value,
        )
    ).first()

    if not otp_record:

        raise AuthError(
            status.HTTP_404_NOT_FOUND,
            "OTP not found",
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

    session.add(
        otp_record,
    )

    session.commit()

    reset_token = create_password_reset_token(
        normalized_email,
    )

    return {
        "reset_token": reset_token,
    }


def handle_complete_password_reset(
    session: Session,
    *,
    reset_token: str,
    new_password: str,
    confirm_password: str,
):

    reset_email = verify_password_reset_token(
        reset_token,
    )

    if not reset_email:

        raise AuthError(
            status.HTTP_401_UNAUTHORIZED,
            ("Invalid or expired reset token"),
        )

    user = get_user_by_email(
        session,
        reset_email,
    )

    if not user:

        raise AuthError(
            status.HTTP_404_NOT_FOUND,
            "User not found",
        )

    local_provider = get_local_auth_provider(
        session,
        user.id,
    )

    if not local_provider:

        raise AuthError(
            status.HTTP_403_FORBIDDEN,
            ("Password reset unavailable for social login accounts"),
        )

    if new_password != confirm_password:

        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            ("Passwords do not match"),
        )

    if not validate_password_strength(
        new_password,
    ):

        raise AuthError(
            status.HTTP_400_BAD_REQUEST,
            "Weak password",
        )

    password_hash = hash_password(
        new_password,
    )

    user.password_hash = password_hash

    # ==========================================
    # Kill all access tokens
    # ==========================================

    user.token_version += 1

    session.add(
        user,
    )

    refresh_sessions = session.exec(
        select(RefreshSession).where(
            RefreshSession.user_id == user.id,
        )
    ).all()

    for refresh_session in refresh_sessions:

        session.delete(
            refresh_session,
        )

    otp_record = session.exec(
        select(OTP).where(
            OTP.email == reset_email,
            OTP.purpose == OTPPurpose.PASSWORD_RESET.value,
        )
    ).first()

    if otp_record:

        session.delete(
            otp_record,
        )

    session.commit()
