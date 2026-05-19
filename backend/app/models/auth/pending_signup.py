import uuid

from datetime import datetime, timezone
from uuid import UUID
from typing import Optional

from sqlmodel import SQLModel, Field


class PendingSignup(SQLModel, table=True):
    __tablename__: str = "pending_signups"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )
    
    existing_user_id: Optional[UUID] = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        unique=True,
    )

    name: str = Field(nullable=False)

    email: str = Field(
        nullable=False,
        unique=True,
        index=True,
    )

    otp_hash: str = Field(nullable=False)

    otp_expires_at: datetime = Field(nullable=False)

    verified: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
