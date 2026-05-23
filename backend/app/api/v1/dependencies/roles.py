from fastapi import (
    Depends,
)

from app.api.v1.dependencies.auth import (
    get_current_user,
)

from app.core.enums import (
    UserRole,
)

from app.core.exceptions.auth import (
    AuthError,
)

from app.models.auth.user import (
    User,
)


def require_roles(
    *allowed_roles: str,
):

    def role_checker(
        current_user: User = Depends(
            get_current_user,
        ),
    ) -> User:

        # Admin bypass

        if current_user.role == UserRole.ADMIN.value:

            return current_user

        if current_user.role not in allowed_roles:

            raise AuthError(
                status_code=403,
                detail=("You do not have permission to access this resource"),
                code="INSUFFICIENT_PERMISSIONS",
            )

        return current_user

    return role_checker
