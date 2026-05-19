from datetime import (
    datetime,
    timezone,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)

from sqlmodel import Session, select
from app.api.v1.dependencies.auth import get_optional_current_user
from app.core.database import (
    get_session,
)

from app.schemas.auth.signup import (
    SignupRequest,
    VerifySignupOTPRequest,
    ResendSignupOTPRequest,
    CompleteSignupRequest,
    UsernameAvailabilityRequest,
)

from app.services.auth.auth_service import (
    normalize_email,
    trim_name,
    validate_name,
    is_email_taken,
    get_pending_signup,
    get_signup_otp,
    normalize_username,
    validate_username,
    is_username_taken,
    validate_public_role,
    generate_username_suggestions,
    generate_profile_color,
)

from app.services.auth.email_templates import (
    generate_otp_email_template,
)

from app.services.auth.email_service import (
    send_email,
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

from app.services.auth.jwt_service import (
    create_signup_token,
    verify_signup_token,
    create_access_token,
)

from app.services.auth.password_service import (
    validate_password_strength,
    hash_password,
)

from app.services.auth.session_service import (
    create_refresh_session,
    set_refresh_cookie,
    build_auth_response,
)

from app.models.auth.pending_signup import (
    PendingSignup,
)

from app.models.auth.user import (
    User,
)

from app.models.auth.refresh_session import (
    RefreshSession,
)

from app.models.auth.auth_provider import (
    AuthProvider,
)

from app.models.auth.otp import (
    OTP,
)

from app.core.enums import (
    AuthProviderType,
    OTPPurpose,
    UserRole,
)

router = APIRouter(
    prefix="/auth",
    tags=["Signup"],
)


@router.post("/signup/request")
def signup_request(
    request: SignupRequest,
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
):

    normalized_email = normalize_email(request.email)

    trimmed_name = trim_name(request.name)

    existing_user_id = None

    if current_user and current_user.is_guest:
        existing_user_id = current_user.id

    if not validate_name(trimmed_name):
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail="Invalid name format",
        )

    if is_email_taken(
        session,
        normalized_email,
    ):
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail="Email already exists",
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
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail="Signup already verified",
        )

    if existing_otp:

        if not is_otp_expired(existing_otp.expires_at):

            if not is_resend_allowed(existing_otp.created_at):
                raise HTTPException(
                    status_code=(status.HTTP_429_TOO_MANY_REQUESTS),
                    detail="OTP resend cooldown active",
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

    email_body = generate_otp_email_template(otp)

    email_sent = send_email(
        recipient=normalized_email,
        subject="Aureon Signup OTP",
        body=email_body,
    )

    if not email_sent:

        raise HTTPException(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            detail="Failed to send OTP email",
        )

    return {
        "message": "OTP sent successfully",
    }


@router.post("/signup/verify")
def verify_signup_otp(
    request: VerifySignupOTPRequest,
    session: Session = Depends(get_session),
):

    normalized_email = normalize_email(request.email,)

    otp_record = get_signup_otp(
        session,
        normalized_email,
    )

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OTP not found",
        )

    pending_signup = get_pending_signup(
        session,
        normalized_email,
    )

    if not pending_signup:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pending signup state corrupted",
        )

    if pending_signup.verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signup already verified",
        )

    if otp_record.verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP already verified",
        )

    if is_otp_expired(
        otp_record.expires_at,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired",
        )

    if has_exceeded_attempts(
        otp_record.attempts,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum OTP attempts exceeded",
        )

    if not verify_otp(
        request.otp,
        otp_record.otp_hash,
    ):

        otp_record.attempts += 1

        session.add(otp_record)

        session.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP",
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
        "message": "OTP verified successfully",
        "signup_token": signup_token,
        "username_suggestions": (username_suggestions),
    }


@router.post("/signup/resend")
def resend_signup_otp(
    request: ResendSignupOTPRequest,
    session: Session = Depends(get_session),
):

    normalized_email = normalize_email(
        request.email,
    )

    otp_record = get_signup_otp(
        session,
        normalized_email,
    )

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OTP not found",
        )

    pending_signup = get_pending_signup(
        session,
        normalized_email,
    )

    if not pending_signup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending signup not found",
        )

    if pending_signup.verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Signup already verified",
        )

    if otp_record.verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP already verified",
        )

    if not is_resend_allowed(
        otp_record.created_at,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="OTP resend cooldown active",
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend OTP email",
        )

    return {
        "message": "OTP resent successfully",
    }


@router.post("/signup/complete")
def complete_signup(
    request: CompleteSignupRequest,
    response: Response,
    session: Session = Depends(get_session),
):

    signup_email = verify_signup_token(request.signup_token)

    if not signup_email:
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail=("Invalid or expired signup token"),
        )

    pending_signup = get_pending_signup(
        session,
        signup_email,
    )

    if not pending_signup:
        raise HTTPException(
            status_code=(status.HTTP_404_NOT_FOUND),
            detail="Pending signup not found",
        )

    if not pending_signup.verified:
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail=("Signup verification required"),
        )

    normalized_username = normalize_username(request.username)

    if not validate_username(normalized_username):
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail="Invalid username format",
        )

    if is_username_taken(
        session,
        normalized_username,
    ):
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail="Username already taken",
        )

    if request.password != request.confirm_password:
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail=("Passwords do not match"),
        )

    if not validate_password_strength(request.password):
        raise HTTPException(
            status_code=(status.HTTP_400_BAD_REQUEST),
            detail="Weak password",
        )

    if not validate_public_role(request.role):
        raise HTTPException(
            status_code=(status.HTTP_403_FORBIDDEN),
            detail="Invalid public role",
        )

    password_hash = hash_password(request.password)

    # ==========================================
    # Guest Upgrade Flow
    # ==========================================
    if pending_signup.existing_user_id:

        if request.role != UserRole.LISTENER.value:
            raise HTTPException(
                status_code=(status.HTTP_403_FORBIDDEN),
                detail=("Guest accounts can only upgrade " "to listener accounts"),
            )

        user = session.get(
            User,
            pending_signup.existing_user_id,
        )

        if not user:
            raise HTTPException(
                status_code=(status.HTTP_404_NOT_FOUND),
                detail="Existing user not found",
            )

        user.name = pending_signup.name
        user.username = request.username
        user.username_normalized = normalized_username
        user.email = pending_signup.email
        user.password_hash = password_hash
        user.role = UserRole.LISTENER.value
        user.is_guest = False
        user.last_login_at = datetime.now(timezone.utc)

        # kill old guest access tokens
        user.token_version += 1

        # revoke old guest refresh sessions
        refresh_sessions = session.exec(
            select(RefreshSession).where(RefreshSession.user_id == user.id)
        ).all()

        for refresh_session in refresh_sessions:
            session.delete(refresh_session)

    # ==========================================
    # Normal Signup Flow
    # ==========================================
    else:

        profile_color = generate_profile_color()

        user = User(
            name=pending_signup.name,
            username=request.username,
            username_normalized=(normalized_username),
            email=pending_signup.email,
            password_hash=password_hash,
            role=request.role,
            is_admin=False,
            is_guest=False,
            profile_color=profile_color,
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
            provider=(AuthProviderType.LOCAL.value),
            provider_user_id=signup_email,
        )

        session.add(auth_provider)

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "token_version": (user.token_version),
        }
    )

    (
        refresh_token,
        refresh_session,
    ) = create_refresh_session(user.id)

    session.add(refresh_session)

    otp_record = get_signup_otp(
        session,
        signup_email,
    )

    if otp_record:
        session.delete(otp_record)

    session.delete(pending_signup)

    session.commit()

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

    normalized_username = normalize_username(request.username)

    if not validate_username(normalized_username):

        return {
            "available": False,
            "valid": False,
        }

    username_taken = is_username_taken(
        session,
        normalized_username,
    )

    return {
        "available": (not username_taken),
        "valid": True,
    }
