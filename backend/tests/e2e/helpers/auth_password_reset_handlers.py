def request_password_reset(
    client,
    *,
    email: str,
):

    return client.post(
        "/api/v1/auth/password-reset/request",
        json={
            "email": email,
        },
    )


def verify_password_reset_otp(
    client,
    *,
    email: str,
    otp: str,
):

    return client.post(
        "/api/v1/auth/password-reset/verify",
        json={
            "email": email,
            "otp": otp,
        },
    )


def complete_password_reset(
    client,
    *,
    reset_token: str,
    new_password: str,
):

    return client.post(
        "/api/v1/auth/password-reset/complete",
        json={
            "reset_token": reset_token,
            "new_password": new_password,
            "confirm_password": new_password,
        },
    )