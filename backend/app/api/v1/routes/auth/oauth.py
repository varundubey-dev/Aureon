from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
)

from fastapi.responses import (
    RedirectResponse,
)

from sqlmodel import Session

from app.api.v1.dependencies.auth import (
    get_optional_session_user,
)

from app.core.config import settings

from app.core.database import (
    get_session,
)

from app.core.rate_limit import (
    limiter,
)

from app.core.security import (
    set_refresh_cookie,
)

from app.models.auth.user import (
    User,
)

from app.schemas.auth.oauth import (
    CompleteOAuthSignupRequest,
)

from app.services.auth.auth_sessions import (
    build_auth_response,
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


@router.get("/google/login")
@limiter.limit("10/minute")
async def google_login(
    request: Request,
    current_user: User | None = Depends(
        get_optional_session_user,
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
@limiter.limit("20/minute")
async def google_callback(
    request: Request,
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

    if not user_info:

        return RedirectResponse(
            url=(
                f"{settings.FRONTEND_URL}"
                f"/oauth/error"
                f"?message=Failed to fetch Google user info"
            ),
            status_code=302,
        )

    result = handle_google_auth_callback(
        session,
        google_user_id=user_info.get("sub"),
        email=user_info.get("email"),
        name=user_info.get("name"),
        email_verified=user_info.get("email_verified"),
        current_user=guest_user,
    )

    # Existing Login

    if result["type"] == "login":

        redirect_response = RedirectResponse(
            url=f"{settings.FRONTEND_URL}/oauth/success",
            status_code=302,
        )

        set_refresh_cookie(
            redirect_response,
            result["refresh_token"],
        )

        return redirect_response

    # New OAuth Signup

    return RedirectResponse(
        url=(
            f"{settings.FRONTEND_URL}"
            f"/oauth/onboarding"
            f"?token={result['oauth_signup_token']}"
        ),
        status_code=302,
    )


@router.post("/google/complete")
@limiter.limit("5/minute")
def complete_google_signup(
    request: Request,
    request_data: CompleteOAuthSignupRequest,
    response: Response,
    session: Session = Depends(get_session),
):

    (
        user,
        access_token,
        refresh_token,
    ) = handle_complete_oauth_signup(
        session,
        oauth_signup_token=request_data.oauth_signup_token,
        role=request_data.role,
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
