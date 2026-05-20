from pydantic import BaseModel


class CompleteOAuthSignupRequest(
    BaseModel,
):
    oauth_signup_token: str
    role: str
