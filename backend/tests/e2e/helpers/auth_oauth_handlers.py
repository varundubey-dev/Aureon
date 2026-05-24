def google_login(client):

    return client.get(
        "/api/v1/auth/google/login",
        follow_redirects=False,
    )


def google_callback(client):

    return client.get(
        "/api/v1/auth/google/callback",
        follow_redirects=False,
    )


def complete_google_signup(
    client,
    *,
    oauth_signup_token: str,
    role: str,
):

    return client.post(
        "/api/v1/auth/google/complete",
        json={
            "oauth_signup_token": oauth_signup_token,
            "role": role,
        },
    )