from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    BackgroundTasks,
)

from sqlmodel import Session

from app.core.database import (
    get_session,
)

from app.services.auth.email_service import (
    send_email,
)

from app.core.exceptions.auth import (
    AuthError,
)

from app.schemas.auth.password_reset import (
    CompletePasswordResetRequest,
    PasswordResetRequest,
    VerifyPasswordResetOTPRequest,
)

from app.services.auth.auth_sessions import (
    clear_refresh_cookie,
)

from app.services.auth.password_reset_service import (
    handle_complete_password_reset,
    handle_password_reset_request,
    handle_password_reset_resend_otp,
    handle_verify_password_reset_otp,
)

router = APIRouter(
    prefix="/auth",
    tags=["Password Reset"],
)


def raise_auth_error(
    exc: AuthError,
):

    raise HTTPException(
        status_code=exc.status_code,
        detail=exc.detail,
    )


@router.post("/password-reset/request")
def request_password_reset(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):

    try:

        result = handle_password_reset_request(
            session=session,
            email=request.email,
        )

    except AuthError as exc:

        raise_auth_error(exc)

    email_data = result.get(
        "email_data",
    )

    if email_data:

        # TODO:
        # Add retry queue + SMTP failure logging later

        background_tasks.add_task(
            send_email,
            recipient=email_data["recipient"],
            subject=email_data["subject"],
            body=email_data["body"],
        )

    return {
        "type": "otp_sent",
        "message": "If account exists, password reset OTP sent",
    }


@router.post("/password-reset/resend")
def resend_password_reset_otp(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):

    try:

        result = handle_password_reset_resend_otp(
            session=session,
            email=request.email,
        )

    except AuthError as exc:

        raise_auth_error(exc)

    email_data = result.get(
        "email_data",
    )

    if email_data:

        # TODO:
        # Add retry queue + SMTP failure logging later

        background_tasks.add_task(
            send_email,
            recipient=email_data["recipient"],
            subject=email_data["subject"],
            body=email_data["body"],
        )

    return {
        "message": "OTP resent successfully",
    }


@router.post("/password-reset/verify")
def verify_password_reset_otp(
    request: VerifyPasswordResetOTPRequest,
    session: Session = Depends(get_session),
):

    try:

        result = handle_verify_password_reset_otp(
            session=session,
            email=request.email,
            otp=request.otp,
        )

    except AuthError as exc:

        raise_auth_error(exc)

    return {
        "type": "otp_verified",
        "message": "OTP verified successfully",
        **result,
    }


@router.post("/password-reset/complete")
def complete_password_reset(
    request: CompletePasswordResetRequest,
    response: Response,
    session: Session = Depends(get_session),
):

    try:

        handle_complete_password_reset(
            session=session,
            reset_token=request.reset_token,
            new_password=request.new_password,
            confirm_password=request.confirm_password,
        )

    except AuthError as exc:

        raise_auth_error(exc)

    clear_refresh_cookie(
        response,
    )

    return {
        "type": "password_reset_completed",
        "message": "Password reset successful. Please login again.",
    }