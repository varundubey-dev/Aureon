from fastapi import (
    Depends,
    HTTPException,
    status,
)

from app.api.v1.dependencies.auth import (
    get_current_user,
)

from app.core.enums import (
    UserRole,
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

        # ==========================================
        # Admin bypass
        # ==========================================

        if (
            current_user.role
            == UserRole.ADMIN.value
        ):

            return current_user

        if (
            current_user.role
            not in allowed_roles
        ):

            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "You do not have permission "
                    "to access this resource"
                ),
            )

        return current_user

    return role_checker