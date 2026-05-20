from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
)

from sqlmodel import Session

from app.api.v1.dependencies.auth import (
    get_optional_current_user,
)

from app.core.config import settings

from app.core.database import (
    get_session,
)

from app.core.exceptions.auth import (
    AuthError,
)

from app.models.auth.user import (
    User,
)

from app.schemas.auth.oauth import (
    CompleteOAuthSignupRequest,
)

from app.services.auth.auth_sessions import (
    build_auth_response,
    set_refresh_cookie,
)

from app.services.auth.oauth_service import (
    handle_complete_oauth_signup,
    handle_google_auth_callback,
)

from app.services.auth.oauth_setup import (
    oauth,
)

router = APIRouter(
    prefix="/auth",
    tags=["OAuth"],
)


def raise_auth_error(
    exc: AuthError,
):

    raise HTTPException(
        status_code=exc.status_code,
        detail=exc.detail,
    )


@router.get("/google/login")
async def google_login(
    request: Request,
    current_user: User | None = Depends(
        get_optional_current_user,
    ),
):

    if current_user and current_user.is_guest:

        request.session["guest_user_id"] = str(
            current_user.id,
        )

    return await oauth.google.authorize_redirect(
        request,
        settings.GOOGLE_REDIRECT_URI,
    )


@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
):

    guest_user = None

    guest_user_id = request.session.get(
        "guest_user_id",
    )

    if guest_user_id:

        guest_user = session.get(
            User,
            guest_user_id,
        )

        request.session.pop(
            "guest_user_id",
            None,
        )

    token = await oauth.google.authorize_access_token(
        request,
    )

    user_info = token.get(
        "userinfo",
    )

    try:

        result = handle_google_auth_callback(
            session,
            google_user_id=user_info.get("sub"),
            email=user_info.get("email"),
            name=user_info.get("name"),
            current_user=guest_user,
        )

    except AuthError as exc:

        raise_auth_error(
            exc,
        )

    # ==========================================
    # Existing Login
    # ==========================================

    if result["type"] == "login":

        set_refresh_cookie(
            response,
            result["refresh_token"],
        )

        return build_auth_response(
            result["user"],
            result["access_token"],
            "Google authentication successful",
        )

    # ==========================================
    # New OAuth Signup
    # ==========================================

    return {
        "message": "OAuth onboarding required",
        "oauth_signup_token": result["oauth_signup_token"],
        "email": result["email"],
        "name": result["name"],
    }


@router.post("/google/complete")
def complete_google_signup(
    request: CompleteOAuthSignupRequest,
    response: Response,
    session: Session = Depends(get_session),
):

    try:

        (
            user,
            access_token,
            refresh_token,
        ) = handle_complete_oauth_signup(
            session,
            oauth_signup_token=request.oauth_signup_token,
            role=request.role,
        )

    except AuthError as exc:

        raise_auth_error(
            exc,
        )

    set_refresh_cookie(
        response,
        refresh_token,
    )

    return build_auth_response(
        user,
        access_token,
        "OAuth signup completed successfully",
    )
