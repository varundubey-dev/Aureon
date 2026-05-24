API_PREFIX = "/api/v1/auth"


def signup_request(
    client,
    *,
    email: str,
    name: str,
):
    return client.post(
        f"{API_PREFIX}/signup/request",
        json={
            "email": email,
            "name": name,
        },
    )


def verify_signup_otp(
    client,
    *,
    email: str,
    otp: str,
):
    return client.post(
        f"{API_PREFIX}/signup/verify",
        json={
            "email": email,
            "otp": otp,
        },
    )


def validate_signup_session(
    client,
    *,
    signup_token: str,
):
    return client.get(
        f"{API_PREFIX}/signup/session/{signup_token}",
    )


def complete_signup(
    client,
    *,
    signup_token: str,
    username: str,
    password: str,
    role: str,
):
    return client.post(
        f"{API_PREFIX}/signup/complete",
        json={
            "signup_token": signup_token,
            "username": username,
            "password": password,
            "confirm_password": password,
            "role": role,
        },
    )