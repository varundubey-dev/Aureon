from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    Cookie,
)

from sqlmodel import Session

from app.core.database import (
    get_session,
)

from app.core.rate_limit import (
    limiter,
)

from app.schemas.auth.login import (
    LoginRequest,
)

from app.models.auth.user import (
    User,
)

from app.api.v1.dependencies.auth import (
    get_current_user,
)

from app.core.security import (
    set_refresh_cookie,
    clear_refresh_cookie,
)

from app.services.auth.auth_sessions import (
    build_auth_response,
)

from app.services.auth.login_service import (
    handle_login,
    handle_refresh_token,
    handle_logout,
)

router = APIRouter(
    prefix="/auth",
    tags=["Login"],
)


@router.post("/login")
@limiter.limit("10/minute")
def login(
    request: Request,
    request_data: LoginRequest,
    response: Response,
    session: Session = Depends(get_session),
):

    (
        user,
        access_token,
        refresh_token,
    ) = handle_login(
        session,
        request_data.identifier,
        request_data.password,
    )

    set_refresh_cookie(
        response,
        refresh_token,
    )

    return {
        "type": "authenticated",
        **build_auth_response(
            user,
            access_token,
            "Login successful",
        ),
    }


@router.post("/refresh")
@limiter.limit("60/minute")
def refresh_access_token(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
    refresh_token: str | None = Cookie(default=None),
):

    (
        user,
        access_token,
        new_refresh_token,
    ) = handle_refresh_token(
        session,
        refresh_token,
    )

    if new_refresh_token:

        set_refresh_cookie(
            response,
            new_refresh_token,
        )

    return {
        "type": "authenticated",
        **build_auth_response(
            user,
            access_token,
        ),
    }


@router.post("/logout")
@limiter.limit("60/minute")
def logout(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
    refresh_token: str | None = Cookie(default=None),
):

    handle_logout(
        session,
        refresh_token,
    )

    clear_refresh_cookie(response)

    return {
        "type": "logged_out",
        "message": "Logout successful",
    }


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
):

    return {
        "type": "authenticated",
        **build_auth_response(
            current_user,
        ),
    }
