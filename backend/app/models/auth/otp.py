import uuid

from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import SQLModel, Field

from app.core.enums import OTPPurpose


class OTP(SQLModel, table=True):
    __tablename__: str = "otp_codes"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )

    email: str = Field(
        nullable=False,
        index=True,
    )

    purpose: str = Field(
        nullable=False,
    )

    otp_hash: str = Field(nullable=False)

    attempts: int = Field(default=0)

    expires_at: datetime = Field(nullable=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    verified: bool = Field(default=False)
