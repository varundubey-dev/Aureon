from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    name: str
    email: EmailStr


class VerifySignupOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class ResendSignupOTPRequest(BaseModel):
    email: EmailStr