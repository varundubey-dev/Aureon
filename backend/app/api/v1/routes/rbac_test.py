from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.api.v1.dependencies.roles import (
    require_roles,
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

router = APIRouter(
    prefix="/rbac",
    tags=["RBAC"],
)


def raise_auth_error(
    exc: AuthError,
):

    raise HTTPException(
        status_code=exc.status_code,
        detail=exc.detail,
    )


@router.get("/listener")
def listener_route(
    current_user: User = Depends(
        require_roles(
            UserRole.LISTENER.value,
        )
    ),
):

    return {
        "message": (
            "Listener route accessed"
        ),
        "user_id": str(current_user.id),
        "role": current_user.role,
    }


@router.get("/artist")
def artist_route(
    current_user: User = Depends(
        require_roles(
            UserRole.ARTIST.value,
        )
    ),
):

    return {
        "message": (
            "Artist route accessed"
        ),
        "user_id": str(current_user.id),
        "role": current_user.role,
    }


@router.get("/admin")
def admin_route(
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN.value,
        )
    ),
):

    return {
        "message": (
            "Admin route accessed"
        ),
        "user_id": str(current_user.id),
        "role": current_user.role,
    }