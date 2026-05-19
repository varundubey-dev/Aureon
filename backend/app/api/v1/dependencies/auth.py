from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.services.auth.jwt_service import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
    )

    try:
        # Decode and validate JWT integrity/signature
        payload = decode_token(token)

        # Access-only restriction prevents refresh tokens
        # from accessing protected API routes.
        if payload.get("type") != "access":
            raise credentials_exception

        # JWT subject stores authenticated user identity.
        user_id = payload.get("sub")

        if not user_id:
            raise credentials_exception

        # TEMPORARY:
        # Currently returning JWT payload directly.
        #
        # Later this dependency should:
        # - query database
        # - validate token_version
        # - verify user existence
        # - verify active account state
        # - return actual user model
        return payload

    except JWTError:
        # Handles:
        # - expired tokens
        # - invalid signatures
        # - malformed JWTs
        raise credentials_exception
