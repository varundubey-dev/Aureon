API_PREFIX = "/api/v1/auth"


def login(
    client,
    *,
    identifier: str,
    password: str,
):
    return client.post(
        f"{API_PREFIX}/login",
        json={
            "identifier": identifier,
            "password": password,
        },
    )