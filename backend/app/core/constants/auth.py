import re

PROFILE_COLORS = [
    "#FF6B6B",
    "#4ECDC4",
    "#45B7D1",
    "#FFA94D",
    "#A78BFA",
]

COMMON_WEAK_PASSWORDS = {
    "password",
    "password123",
    "12345678",
    "qwerty123",
    "admin123",
}

PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{8,}$")
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
NAME_REGEX = re.compile(r"^[A-Za-z]+(?:[ '-][A-Za-z]+)*$")
USERNAME_REGEX = re.compile(r"^(?!.*__)(?!.*\.\.)(?!\d+$)[a-zA-Z0-9._]+$")
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30

NAME_MIN_LENGTH = 3
NAME_MAX_LENGTH = 30

PASSWORD_MIN_LENGTH = 8