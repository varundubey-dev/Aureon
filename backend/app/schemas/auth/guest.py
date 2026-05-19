from pydantic import BaseModel


class UpgradeGuestRequest(BaseModel):
    email: str
    username: str
    password: str
    confirm_password: str
