from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
)

from sqlmodel import Session

from app.api.v1.dependencies.auth import (
    get_optional_current_user,
)

from app.core.database import (
    get_session,
)

from app.core.exceptions.auth import (
    AuthError,
)

from app.models.auth.user import (
    User,
)

from app.schemas.auth.signup import (
    CompleteSignupRequest,
    ResendSignupOTPRequest,
    SignupRequest,
    UsernameAvailabilityRequest,
    VerifySignupOTPRequest,
)

from app.services.auth.auth_queries import (
    is_username_taken,
)

from app.services.auth.auth_sessions import (
    build_auth_response,
    set_refresh_cookie,
)

from app.services.auth.auth_validators import (
    normalize_username,
    validate_username,
)

from app.services.auth.signup_service import (
    handle_complete_signup,
    handle_resend_signup_otp,
    handle_signup_request,
    handle_verify_signup_otp,
)

router = APIRouter(
    prefix="/auth",
    tags=["Signup"],
)


def raise_auth_error(
    exc: AuthError,
):

    raise HTTPException(
        status_code=exc.status_code,
        detail=exc.detail,
    )


@router.post("/signup/request")
def signup_request(
    request: SignupRequest,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(
        get_optional_current_user,
    ),
):

    existing_user_id = None

    if current_user and current_user.is_guest:
        existing_user_id = current_user.id

    try:

        result = handle_signup_request(
            session=session,
            email=request.email,
            name=request.name,
            existing_user_id=existing_user_id,
        )

    except AuthError as exc:

        raise_auth_error(exc)

    # ==========================================
    # Existing OAuth User Local Setup Flow
    # ==========================================

    if result:

        return result

    # ==========================================
    # Normal OTP Signup Flow
    # ==========================================

    return {
        "type": "otp_verification",
        "message": "OTP sent successfully",
    }


@router.post("/signup/verify")
def verify_signup_otp(
    request: VerifySignupOTPRequest,
    session: Session = Depends(get_session),
):

    try:

        result = handle_verify_signup_otp(
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


@router.post("/signup/resend")
def resend_signup_otp(
    request: ResendSignupOTPRequest,
    session: Session = Depends(get_session),
):

    try:

        handle_resend_signup_otp(
            session=session,
            email=request.email,
        )

    except AuthError as exc:
        raise_auth_error(exc)

    return {
        "message": "OTP resent successfully",
    }


@router.post("/signup/complete")
def complete_signup(
    request: CompleteSignupRequest,
    response: Response,
    session: Session = Depends(get_session),
):

    try:

        (
            user,
            access_token,
            refresh_token,
        ) = handle_complete_signup(
            session=session,
            signup_token=request.signup_token,
            username=request.username,
            password=request.password,
            confirm_password=request.confirm_password,
            role=request.role,
        )

    except AuthError as exc:
        raise_auth_error(exc)

    set_refresh_cookie(
        response,
        refresh_token,
    )

    return build_auth_response(
        user,
        access_token,
        "Signup completed successfully",
    )


@router.post("/username/check")
def check_username_availability(
    request: UsernameAvailabilityRequest,
    session: Session = Depends(get_session),
):

    normalized_username = normalize_username(
        request.username,
    )

    if not validate_username(
        normalized_username,
    ):

        return {
            "available": False,
            "valid": False,
        }

    return {
        "available": not is_username_taken(
            session,
            normalized_username,
        ),
        "valid": True,
    }
