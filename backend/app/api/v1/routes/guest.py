from fastapi import (
    APIRouter,
    Depends,
    Response,
)

from sqlmodel import Session

from app.core.database import get_session

from app.services.auth.auth_utils import (
    generate_profile_color,
)

from app.services.auth.auth_tokens import (
    create_access_token,
)

from app.services.auth.auth_sessions import (
    build_auth_response,
    create_refresh_session,
    set_refresh_cookie,
)

from app.services.auth.guest_service import (
    create_guest_user,
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

    guest_user = create_guest_user()
    guest_user.profile_color = generate_profile_color()

    session.add(guest_user)
    session.flush()

    access_token = create_access_token(
        {
            "sub": str(guest_user.id),
            "token_version": guest_user.token_version,
        }
    )

    (
        refresh_token,
        refresh_session,
    ) = create_refresh_session(
        guest_user.id,
    )

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
