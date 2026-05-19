from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str
    FRONTEND_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    SIGNUP_TOKEN_EXPIRE_MINUTES: int

    OTP_EXPIRATION_MINUTES: int
    OTP_RESEND_COOLDOWN_SECONDS: int
    OTP_MAX_ATTEMPTS: int

    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str


settings = Settings.model_validate({})
