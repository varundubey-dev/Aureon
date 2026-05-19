from datetime import (
    datetime,
    timezone,
)
from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
    Cookie,
)

from sqlmodel import Session

from app.core.database import (
    get_session,
)

from app.schemas.auth.login import (
    LoginRequest,
)

from app.services.auth.auth_service import (
    get_user_by_identifier,
)

from app.services.auth.password_service import (
    verify_password,
)

from app.services.auth.jwt_service import (
    create_access_token,
    verify_refresh_token,
)

from app.services.auth.session_service import (
    create_refresh_session,
    set_refresh_cookie,
    clear_refresh_cookie,
    build_auth_response,
    get_refresh_session_by_id,
)

from app.models.auth.user import (
    User,
)

from app.api.v1.dependencies.auth import (
    get_current_user,
)

router = APIRouter(
    prefix="/auth",
    tags=["Login"],
)


@router.post("/login")
def login(
    request: LoginRequest,
    response: Response,
    session: Session = Depends(get_session),
):

    user = get_user_by_identifier(
        session,
        request.identifier,
    )

    if not user:
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="Invalid credentials",
        )

    if not user.password_hash:
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="Invalid credentials",
        )

    if not verify_password(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="Invalid credentials",
        )

    user.last_login_at = datetime.now(timezone.utc)

    session.add(user)

    access_token = create_access_token(
        {
            "sub": str(user.id),
        }
    )

    (
        refresh_token,
        refresh_session,
    ) = create_refresh_session(user.id)

    session.add(refresh_session)

    session.commit()

    set_refresh_cookie(
        response,
        refresh_token,
    )

    return build_auth_response(
        user,
        access_token,
        "Login successful",
    )


@router.post("/refresh")
def refresh_access_token(
    response: Response,
    session: Session = Depends(get_session),
    refresh_token: str | None = Cookie(default=None),
):

    if not refresh_token:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="Refresh token missing",
        )

    payload = verify_refresh_token(refresh_token)

    if not payload:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")

    session_id = payload.get("jti")

    if not user_id or not session_id:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="Invalid refresh token",
        )

    user_id = UUID(user_id)

    session_id = UUID(session_id)

    refresh_session = get_refresh_session_by_id(
        session,
        session_id,
    )

    if not refresh_session:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="Refresh session invalid",
        )

    if not verify_password(
        refresh_token,
        refresh_session.token_hash,
    ):
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="Refresh session invalid",
        )

    if refresh_session.user_id != user_id:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="Refresh session invalid",
        )

    if refresh_session.expires_at < datetime.now(timezone.utc):
        clear_refresh_cookie(response)
        session.delete(refresh_session)

        session.commit()

        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="Refresh token expired",
        )

    # Refresh token rotation:
    # old session dies immediately
    session.delete(refresh_session)

    access_token = create_access_token(
        {
            "sub": str(user_id),
        }
    )

    (
        new_refresh_token,
        new_refresh_session,
    ) = create_refresh_session(user_id)

    session.add(new_refresh_session)

    session.commit()

    set_refresh_cookie(
        response,
        new_refresh_token,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(
    response: Response,
    session: Session = Depends(get_session),
    refresh_token: str | None = Cookie(default=None),
):

    if refresh_token:

        payload = verify_refresh_token(refresh_token)

        if payload:

            session_id = payload.get("jti")

            if session_id:

                refresh_session = get_refresh_session_by_id(
                    session,
                    UUID(session_id),
                )

                if refresh_session:

                    session.delete(refresh_session)

                    session.commit()

    clear_refresh_cookie(response)

    return {
        "message": "Logout successful",
    }


@router.get("/me")
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
):

    return build_auth_response(
        current_user
    )