from pydantic import (
    BaseModel,
    EmailStr,
)


class PasswordResetRequest(
    BaseModel
):
    email: EmailStr


class VerifyPasswordResetOTPRequest(
    BaseModel
):
    email: EmailStr
    otp: str


class CompletePasswordResetRequest(
    BaseModel
):
    reset_token: str
    new_password: str
    confirm_password: str