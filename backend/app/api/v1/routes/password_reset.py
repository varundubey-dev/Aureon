from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
)

from sqlmodel import Session

from app.core.database import (
    get_session,
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
    session: Session = Depends(get_session),
):

    try:

        handle_password_reset_request(
            session=session,
            email=request.email,
        )

    except AuthError as exc:
        raise_auth_error(exc)

    return {
        "message": "If account exists, password reset OTP sent",
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
        "message": "Password reset successful. Please login again.",
    }
