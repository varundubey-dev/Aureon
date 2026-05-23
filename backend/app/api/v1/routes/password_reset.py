from fastapi import (
    APIRouter,
    Depends,
    Response,
    BackgroundTasks,
    Request,
)

from sqlmodel import Session

from app.core.database import (
    get_session,
)

from app.core.rate_limit import (
    limiter,
)

from app.schemas.auth.password_reset import (
    CompletePasswordResetRequest,
    PasswordResetRequest,
    VerifyPasswordResetOTPRequest,
)

from app.services.auth.email_service import (
    send_email,
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


@router.post("/password-reset/request")
@limiter.limit("5/minute")
def request_password_reset(
    request: Request,
    request_data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):

    result = handle_password_reset_request(
        session=session,
        email=request_data.email,
    )

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
@limiter.limit("3/minute")
def resend_password_reset_otp(
    request: Request,
    request_data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):

    result = handle_password_reset_resend_otp(
        session=session,
        email=request_data.email,
    )

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
@limiter.limit("10/minute")
def verify_password_reset_otp(
    request: Request,
    request_data: VerifyPasswordResetOTPRequest,
    session: Session = Depends(get_session),
):

    result = handle_verify_password_reset_otp(
        session=session,
        email=request_data.email,
        otp=request_data.otp,
    )

    return {
        "type": "otp_verified",
        "message": "OTP verified successfully",
        **result,
    }


@router.post("/password-reset/complete")
@limiter.limit("5/minute")
def complete_password_reset(
    request: Request,
    request_data: CompletePasswordResetRequest,
    response: Response,
    session: Session = Depends(get_session),
):

    handle_complete_password_reset(
        session=session,
        reset_token=request_data.reset_token,
        new_password=request_data.new_password,
        confirm_password=request_data.confirm_password,
    )

    clear_refresh_cookie(
        response,
    )

    return {
        "type": "password_reset_completed",
        "message": "Password reset successful. Please login again.",
    }
