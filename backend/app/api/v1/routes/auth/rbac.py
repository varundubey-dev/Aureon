from fastapi import (
    APIRouter,
    Depends,
)

from app.api.v1.dependencies.roles import (
    require_roles,
)

from app.core.enums import (
    UserRole,
)

from app.models.auth.user import (
    User,
)

router = APIRouter(
    prefix="/rbac",
    tags=["RBAC"],
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
        "message": "Listener route accessed",
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
        "message": "Artist route accessed",
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
        "message": "Admin route accessed",
        "user_id": str(current_user.id),
        "role": current_user.role,
    }
