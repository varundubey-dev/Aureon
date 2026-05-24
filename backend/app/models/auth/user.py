import uuid

from datetime import datetime
from app.utils.datetime import (
    get_utc_now,
)
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

    name: Optional[str] = Field(
        default=None,
        nullable=True,
    )

    username: Optional[str] = Field(
        default=None,
        unique=True,
        index=True,
        nullable=True,
    )

    username_normalized: Optional[str] = Field(
        default=None,
        unique=True,
        index=True,
        nullable=True,
    )

    email: Optional[str] = Field(
        default=None,
        unique=True,
        index=True,
        nullable=True,
    )

    password_hash: Optional[str] = Field(
        default=None
    )

    role: str = Field(
        default=UserRole.LISTENER.value,
        nullable=False,
    )

    is_admin: bool = Field(default=False)

    is_guest: bool = Field(default=False)

    profile_color: str = Field(nullable=False)

    token_version: int = Field(default=0)

    created_at: datetime = Field(default_factory=lambda: get_utc_now())

    last_login_at: Optional[datetime] = Field(default=None)
