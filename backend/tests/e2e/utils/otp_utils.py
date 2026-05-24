import re


def extract_otp(email_body: str) -> str:

    match = re.search(
        r"\b(\d{6})\b",
        email_body,
    )

    assert match is not None

    return match.group(1)