from fastapi import (
    APIRouter,
    Depends,
    Response,
    BackgroundTasks,
    Request,
)

from sqlmodel import Session

from app.api.v1.dependencies.auth import (
    get_optional_current_user,
)

from app.core.database import (
    get_session,
)

from app.core.rate_limit import (
    limiter,
)

from app.services.email.email_service import (
    send_email,
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
)

from app.core.security import (
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
    validate_signup_session,
)

router = APIRouter(
    prefix="/auth",
    tags=["Signup"],
)


@router.post("/signup/request")
@limiter.limit("5/minute")
def signup_request(
    request: Request,
    request_data: SignupRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(
        get_optional_current_user,
    ),
):

    existing_user_id = None

    if current_user and current_user.is_guest:
        existing_user_id = current_user.id

    result = handle_signup_request(
        session=session,
        email=request_data.email,
        name=request_data.name,
        existing_user_id=existing_user_id,
    )

    email_data = result.pop(
        "email_data",
        None,
    )

    if email_data:

        # TODO:
        # Add proper retry queue later
        # Log SMTP failures
        # Move to Celery/Redis worker eventually

        background_tasks.add_task(
            send_email,
            recipient=email_data["recipient"],
            subject=email_data["subject"],
            body=email_data["body"],
        )

    return result


@router.post("/signup/verify")
@limiter.limit("10/minute")
def verify_signup_otp(
    request: Request,
    request_data: VerifySignupOTPRequest,
    session: Session = Depends(get_session),
):

    result = handle_verify_signup_otp(
        session=session,
        email=request_data.email,
        otp=request_data.otp,
    )

    return {
        "message": "OTP verified successfully",
        **result,
    }


@router.get("/signup/session/{signup_token}")
@limiter.limit("20/minute")
def validate_signup(
    request: Request,
    signup_token: str,
    session: Session = Depends(get_session),
):

    result = validate_signup_session(
        session=session,
        signup_token=signup_token,
    )

    return {
        "message": "Signup session valid",
        **result,
    }


@router.post("/signup/resend")
@limiter.limit("3/minute")
def resend_signup_otp(
    request: Request,
    request_data: ResendSignupOTPRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):

    result = handle_resend_signup_otp(
        session=session,
        email=request_data.email,
    )

    email_data = result.get(
        "email_data",
    )

    if email_data:

        # TODO:
        # Add retry queue + logging later

        background_tasks.add_task(
            send_email,
            recipient=email_data["recipient"],
            subject=email_data["subject"],
            body=email_data["body"],
        )

    return {
        "message": "OTP resent successfully",
    }


@router.post("/signup/complete")
@limiter.limit("10/minute")
def complete_signup(
    request: Request,
    request_data: CompleteSignupRequest,
    response: Response,
    session: Session = Depends(get_session),
):

    (
        user,
        access_token,
        refresh_token,
    ) = handle_complete_signup(
        session=session,
        signup_token=request_data.signup_token,
        username=request_data.username,
        password=request_data.password,
        confirm_password=request_data.confirm_password,
        role=request_data.role,
    )

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
@limiter.limit("30/minute")
def check_username_availability(
    request: Request,
    request_data: UsernameAvailabilityRequest,
    session: Session = Depends(get_session),
):

    normalized_username = normalize_username(
        request_data.username,
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
