import uuid

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlmodel import SQLModel, Field

from app.core.enums import UserRole


class User(SQLModel, table=True):
    __tablename__: str = "users"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )

    name: str = Field(nullable=False)

    username: str = Field(
        index=True,
        nullable=False,
    )

    username_normalized: str = Field(
        unique=True,
        index=True,
        nullable=False,
    )

    email: str = Field(
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Optional[str] = Field(default=None)

    role: str = Field(
        default=UserRole.LISTENER.value,
        nullable=False,
    )

    is_admin: bool = Field(default=False)

    is_guest: bool = Field(default=False)

    profile_color: str = Field(nullable=False)

    token_version: int = Field(default=0)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    last_login_at: Optional[datetime] = Field(default=None)
