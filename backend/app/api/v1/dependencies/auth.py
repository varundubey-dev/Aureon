from fastapi import (
    Depends,
    HTTPException,
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

from app.services.auth.auth_tokens import (
    verify_access_token,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


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
            status_code=401,
            detail="Authentication required",
        )

    payload = verify_access_token(
        token,
    )

    if not payload:

        raise HTTPException(
            status_code=401,
            detail="Invalid access token",
        )

    user_id = payload.get(
        "sub",
    )

    user = session.get(
        User,
        user_id,
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="User not found",
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

    payload = verify_access_token(
        token,
    )

    if not payload:
        return None

    user_id = payload.get(
        "sub",
    )

    return session.get(
        User,
        user_id,
    )
