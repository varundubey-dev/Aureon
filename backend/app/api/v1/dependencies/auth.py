from fastapi import (
    Depends,
    HTTPException,
    Request,
    status,
)

from fastapi.security import (
    OAuth2PasswordBearer,
)

from sqlmodel import Session

from app.core.database import (
    get_session,
)

from app.models.auth.user import (
    User,
)

from app.services.auth.auth_sessions import (
    get_refresh_session_by_id,
)

from app.services.auth.auth_tokens import (
    verify_access_token,
    verify_refresh_token,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


def validate_access_token_user(
    session: Session,
    token: str,
) -> User | None:

    payload = verify_access_token(
        token,
    )

    if not payload:
        return None

    user_id = payload.get(
        "sub",
    )

    user = session.get(
        User,
        user_id,
    )

    if not user:
        return None

    if payload.get("token_version") != user.token_version:
        return None

    return user


def get_current_user(
    token: str | None = Depends(
        oauth2_scheme,
    ),
    session: Session = Depends(
        get_session,
    ),
) -> User:

    if not token:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    user = validate_access_token_user(
        session,
        token,
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    return user


def get_optional_current_user(
    token: str | None = Depends(
        oauth2_scheme,
    ),
    session: Session = Depends(
        get_session,
    ),
) -> User | None:

    if not token:
        return None

    return validate_access_token_user(
        session,
        token,
    )


# Browser session restore dependency
# Used ONLY for OAuth/session flows


def get_optional_session_user(
    request: Request,
    token: str | None = Depends(
        oauth2_scheme,
    ),
    session: Session = Depends(
        get_session,
    ),
) -> User | None:

    # Try access token first

    if token:

        user = validate_access_token_user(
            session,
            token,
        )

        if user:
            return user

        # Fallback to refresh cookie

    refresh_token = request.cookies.get(
        "refresh_token",
    )

    if not refresh_token:
        return None

    payload = verify_refresh_token(
        refresh_token,
    )

    if not payload:
        return None

    session_id = payload.get(
        "jti",
    )

    user_id = payload.get(
        "sub",
    )

    if not session_id or not user_id:
        return None

    refresh_session = get_refresh_session_by_id(
        session,
        session_id,
    )

    if not refresh_session:
        return None

    user = session.get(
        User,
        user_id,
    )

    if not user:
        return None

    return user
