from uuid import UUID

from fastapi import (
    Depends,
    HTTPException,
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

from app.services.auth.jwt_service import (
    verify_access_token,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:

    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="Invalid access token",
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="Invalid access token",
        )

    user = session.get(
        User,
        UUID(user_id),
    )

    if not user:
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="User not found",
        )

    token_version = payload.get("token_version")

    if token_version != user.token_version:
        raise HTTPException(
            status_code=(status.HTTP_401_UNAUTHORIZED),
            detail="Token expired",
        )

    return user
