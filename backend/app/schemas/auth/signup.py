from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    name: str
    email: EmailStr


class VerifySignupOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class ResendSignupOTPRequest(BaseModel):
    email: EmailStr
    
class CompleteSignupRequest(BaseModel):
    signup_token: str
    username: str
    password: str
    confirm_password: str
    role: str

class UsernameAvailabilityRequest(BaseModel):
    username: str