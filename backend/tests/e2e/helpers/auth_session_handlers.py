API_PREFIX = "/api/v1/auth"


def refresh_auth_session(client):
    return client.post(
        f"{API_PREFIX}/refresh",
    )


def logout(client):
    return client.post(
        f"{API_PREFIX}/logout",
    )