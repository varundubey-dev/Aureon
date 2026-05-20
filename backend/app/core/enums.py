from enum import Enum


class UserRole(str, Enum):
    LISTENER = "listener"
    ARTIST = "artist"
    ADMIN = "admin"


class AuthProviderType(str, Enum):
    LOCAL = "local"
    GOOGLE = "google"


class OTPPurpose(str, Enum):
    SIGNUP = "signup"
    PASSWORD_RESET = "password_reset"
