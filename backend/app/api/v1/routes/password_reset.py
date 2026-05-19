from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)

from sqlmodel import Session, select

from app.core.database import (
    get_session,
)

from app.schemas.auth.password_reset import (
    PasswordResetRequest,
    VerifyPasswordResetOTPRequest,
    CompletePasswordResetRequest,
)

from app.services.auth.auth_service import (
    normalize_email,
    get_user_by_email,
)

from app.services.auth.otp_service import (
    generate_otp,
    hash_otp,
    verify_otp,
    create_otp_expiration,
    is_otp_expired,
    is_resend_allowed,
    has_exceeded_attempts,
    reset_otp_record,
)

from app.services.auth.email_service import (
    send_email,
)

from app.services.auth.email_templates import (
    generate_password_reset_email_template,
)

from app.services.auth.jwt_service import (
    create_password_reset_token,
    verify_password_reset_token,
)

from app.services.auth.session_service import(
    clear_refresh_cookie,
)

from app.services.auth.password_service import (
    validate_password_strength,
    hash_password,
)

from app.models.auth.otp import (
    OTP,
)

from app.models.auth.refresh_session import (
    RefreshSession,
)

from app.core.enums import (
    OTPPurpose,
)

router = APIRouter(
    prefix="/auth",
    tags=["Password Reset"],
)


@router.post("/password-reset/request")
def request_password_reset(
    request: PasswordResetRequest,
    session: Session = Depends(get_session),
):

    normalized_email = normalize_email(request.email)

    user = get_user_by_email(
        session,
        normalized_email,
    )

    # Silent success:
    # never reveal account existence.
    if not user:

        return {
            "message": ("If account exists, " "password reset OTP sent"),
        }

    existing_otp = session.exec(
        select(OTP).where(
            OTP.email == normalized_email,
            OTP.purpose == OTPPurpose.PASSWORD_RESET.value,
        )
    ).first()

    if existing_otp:

        if not is_otp_expired(existing_otp.expires_at):

            if not is_resend_allowed(existing_otp.created_at):
                raise HTTPException(
                    status_code=(status.HTTP_429_TOO_MANY_REQUESTS),
                    detail=("OTP resend cooldown active"),
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
            purpose=(OTPPurpose.PASSWORD_RESET.value),
            otp_hash=hashed_otp,
            expires_at=otp_expiration,
        )

    session.add(otp_record)

    session.commit()

    email_body = generate_password_reset_email_template(otp)

    send_email(
        recipient=normalized_email,
        subject="Aureon Password Reset OTP",
        body=email_body,
    )

    return {
        "message": ("If account exists, " "password reset OTP sent"),
    }


@router.post("/password-reset/verify")
def verify_password_reset_otp(
    request: VerifyPasswordResetOTPRequest,
    session: Session = Depends(get_session),
):

    normalized_email = normalize_email(request.email)

    otp_record = session.exec(
        select(OTP).where(
            OTP.email == normalized_email,
            OTP.purpose == OTPPurpose.PASSWORD_RESET.value,
        )
    ).first()

    if not otp_record:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail="OTP not found",
        )

    if otp_record.verified:
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail="OTP already verified",
        )

    if is_otp_expired(otp_record.expires_at):
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail="OTP expired",
        )

    if has_exceeded_attempts(otp_record.attempts):
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail=("Maximum OTP attempts exceeded"),
        )

    if not verify_otp(
        request.otp,
        otp_record.otp_hash,
    ):

        otp_record.attempts += 1

        session.add(otp_record)

        session.commit()

        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail="Invalid OTP",
        )

    otp_record.verified = True

    session.add(otp_record)

    session.commit()

    reset_token = create_password_reset_token(normalized_email)

    return {
        "message": ("OTP verified successfully"),
        "reset_token": reset_token,
    }


@router.post("/password-reset/complete")
def complete_password_reset(
    request: CompletePasswordResetRequest,
    response: Response,
    session: Session = Depends(get_session),
):

    reset_email = verify_password_reset_token(request.reset_token)

    if not reset_email:
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail=("Invalid or expired reset token"),
        )

    user = get_user_by_email(
        session,
        reset_email,
    )

    if not user:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail="User not found",
        )

    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail="Passwords do not match",
        )

    if not validate_password_strength(request.new_password):
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail="Weak password",
        )

    password_hash = hash_password(request.new_password)

    user.password_hash = password_hash

    # Global auth invalidation:
    # all existing access tokens die.
    user.token_version += 1

    session.add(user)

    refresh_sessions = session.exec(
        select(RefreshSession).where(RefreshSession.user_id == user.id)
    ).all()

    for refresh_session in refresh_sessions:

        session.delete(refresh_session)

    otp_record = session.exec(
        select(OTP).where(
            OTP.email == reset_email,
            OTP.purpose == OTPPurpose.PASSWORD_RESET.value,
        )
    ).first()

    if otp_record:

        session.delete(otp_record)
        
    clear_refresh_cookie(response)
    
    session.commit()

    return {
        "message": ("Password reset successful. " "Please login again."),
    }
