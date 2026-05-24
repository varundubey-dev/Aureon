# =========================================================
# RBAC Dependency Tests
# =========================================================
#
# This file tests:
#
# require_roles()
#
# Covered areas:
#
# 1. Allowed role access
#    - Listener access
#    - Artist access
#
# 2. Permission rejection
#    - Unauthorized role rejection
#
# 3. Admin bypass
#    - Admin ignores role restrictions
#
# 4. Authentication dependency integration
#    - Missing token rejection
#    - Invalid token rejection
#
# NOTE:
#
# - This file tests ONLY RBAC dependency behavior.
# - Route integration is tested separately.
#
# =========================================================

from app.core.enums import (
    AuthProviderType,
    UserRole,
)

from app.models.auth.auth_provider import (
    AuthProvider,
)

from app.models.auth.user import (
    User,
)

from app.services.auth.auth_tokens import (
    create_access_token,
)

from app.services.auth.password_service import (
    hash_password,
)

# =========================================================
# Helpers
# =========================================================


def create_user(
    session,
    *,
    role=UserRole.LISTENER.value,
    email="rbac@example.com",
    username="rbacuser",
):

    user = User(
        name="RBAC User",
        username=username,
        username_normalized=username,
        email=email,
        password_hash=hash_password(
            "StrongPassword123!",
        ),
        role=role,
        is_admin=(role == UserRole.ADMIN.value),
        is_guest=False,
        profile_color="#ffffff",
        token_version=0,
    )

    session.add(user)
    session.flush()

    provider = AuthProvider(
        user_id=user.id,
        provider=AuthProviderType.LOCAL.value,
        provider_user_id=email,
    )

    session.add(provider)
    session.commit()

    return user


def authenticated_headers(
    access_token,
):

    return {
        "Authorization": f"Bearer {access_token}",
    }


def create_access_token_for_user(
    user,
):

    return create_access_token(
        {
            "sub": str(user.id),
            "token_version": user.token_version,
        }
    )


# =========================================================
# Allowed Role Access
# =========================================================


def test_listener_can_access_listener_route(
    client,
    session,
):

    user = create_user(
        session,
        role=UserRole.LISTENER.value,
    )

    access_token = create_access_token_for_user(
        user,
    )

    response = client.get(
        "/api/v1/rbac/listener",
        headers=authenticated_headers(
            access_token,
        ),
    )

    assert response.status_code == 200


def test_artist_can_access_artist_route(
    client,
    session,
):

    user = create_user(
        session,
        role=UserRole.ARTIST.value,
        email="artist@example.com",
        username="artistuser",
    )

    access_token = create_access_token_for_user(
        user,
    )

    response = client.get(
        "/api/v1/rbac/artist",
        headers=authenticated_headers(
            access_token,
        ),
    )

    assert response.status_code == 200


# =========================================================
# Permission Rejection
# =========================================================


def test_listener_cannot_access_artist_route(
    client,
    session,
):

    user = create_user(
        session,
        role=UserRole.LISTENER.value,
    )

    access_token = create_access_token_for_user(
        user,
    )

    response = client.get(
        "/api/v1/rbac/artist",
        headers=authenticated_headers(
            access_token,
        ),
    )

    assert response.status_code == 403

    data = response.json()

    assert data["code"] == "INSUFFICIENT_PERMISSIONS"


def test_artist_cannot_access_admin_route(
    client,
    session,
):

    user = create_user(
        session,
        role=UserRole.ARTIST.value,
    )

    access_token = create_access_token_for_user(
        user,
    )

    response = client.get(
        "/api/v1/rbac/admin",
        headers=authenticated_headers(
            access_token,
        ),
    )

    assert response.status_code == 403

    data = response.json()

    assert data["code"] == "INSUFFICIENT_PERMISSIONS"


# =========================================================
# Admin Bypass
# =========================================================


def test_admin_can_access_all_routes(
    client,
    session,
):

    admin = create_user(
        session,
        role=UserRole.ADMIN.value,
        email="admin@example.com",
        username="adminuser",
    )

    access_token = create_access_token_for_user(
        admin,
    )

    listener_response = client.get(
        "/api/v1/rbac/listener",
        headers=authenticated_headers(
            access_token,
        ),
    )

    artist_response = client.get(
        "/api/v1/rbac/artist",
        headers=authenticated_headers(
            access_token,
        ),
    )

    admin_response = client.get(
        "/api/v1/rbac/admin",
        headers=authenticated_headers(
            access_token,
        ),
    )

    assert listener_response.status_code == 200
    assert artist_response.status_code == 200
    assert admin_response.status_code == 200


# =========================================================
# Authentication Integration
# =========================================================


def test_rbac_missing_access_token(
    client,
):

    response = client.get(
        "/api/v1/rbac/listener",
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "AUTH_REQUIRED"


def test_rbac_invalid_access_token(
    client,
):

    response = client.get(
        "/api/v1/rbac/listener",
        headers=authenticated_headers(
            "invalid-token",
        ),
    )

    assert response.status_code == 401

    data = response.json()

    assert data["code"] == "INVALID_ACCESS_TOKEN"
