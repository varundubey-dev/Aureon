from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    Cookie,
)

from sqlmodel import Session

from app.core.database import (
    get_session,
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

from app.services.auth.auth_sessions import (
    set_refresh_cookie,
    clear_refresh_cookie,
    build_auth_response,
)

from app.services.auth.login_service import (
    handle_login,
    handle_refresh_token,
    handle_logout,
)

from app.core.exceptions.auth import (
    AuthError,
)

router = APIRouter(
    prefix="/auth",
    tags=["Login"],
)


def raise_auth_error(
    exc: AuthError,
):

    raise HTTPException(
        status_code=exc.status_code,
        detail=exc.detail,
    )


@router.post("/login")
def login(
    request: LoginRequest,
    response: Response,
    session: Session = Depends(get_session),
):

    try:

        (
            user,
            access_token,
            refresh_token,
        ) = handle_login(
            session,
            request.identifier,
            request.password,
        )

    except AuthError as exc:
        raise_auth_error(exc)

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
def refresh_access_token(
    response: Response,
    session: Session = Depends(get_session),
    refresh_token: str | None = Cookie(default=None),
):

    try:

        (
            access_token,
            new_refresh_token,
        ) = handle_refresh_token(
            session,
            refresh_token,
        )

    except AuthError as exc:

        clear_refresh_cookie(response)

        raise_auth_error(exc)

    set_refresh_cookie(
        response,
        new_refresh_token,
    )

    return {
        "type": "token_refreshed",
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(
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
