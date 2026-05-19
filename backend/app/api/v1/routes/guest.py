from datetime import (
    datetime,
    timezone,
)

from fastapi import (
    APIRouter,
    Depends,
    Response,
)

from sqlmodel import Session

from app.core.database import (
    get_session,
)

from app.core.enums import (
    UserRole,
)

from app.models.auth.user import (
    User,
)

from app.services.auth.auth_service import (
    generate_profile_color,
)

from app.services.auth.jwt_service import (
    create_access_token,
)

from app.services.auth.session_service import (
    create_refresh_session,
    set_refresh_cookie,
    build_auth_response,
)

router = APIRouter(
    prefix="/auth",
    tags=["Guest"],
)


@router.post("/guest")
def create_guest_account(
    response: Response,
    session: Session = Depends(get_session),
):

    guest_name = "Guest"

    guest_user = User(
        name=guest_name,
        username=None,
        username_normalized=None,
        email=None,
        password_hash=None,
        role=UserRole.LISTENER.value,
        is_admin=False,
        is_guest=True,
        profile_color=generate_profile_color(),
        token_version=0,
        created_at=datetime.now(timezone.utc),
        last_login_at=datetime.now(timezone.utc),
    )

    session.add(guest_user)

    session.flush()

    access_token = create_access_token(
        {
            "sub": str(guest_user.id),
            "token_version": (guest_user.token_version),
        }
    )

    (
        refresh_token,
        refresh_session,
    ) = create_refresh_session(guest_user.id)

    session.add(refresh_session)

    session.commit()

    set_refresh_cookie(
        response,
        refresh_token,
    )

    return build_auth_response(
        guest_user,
        access_token,
        "Guest account created",
    )
