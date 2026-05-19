import uuid

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field

from app.core.enums import AuthProviderType


class AuthProvider(SQLModel, table=True):
    __tablename__: str = "auth_providers"

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_provider_provider_user_id",
        ),
    )

    id: UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )

    user_id: UUID = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
    )

    provider: str = Field(
        default=AuthProviderType.LOCAL.value,
        nullable=False,
        index=True,
    )

    provider_user_id: str = Field(
        nullable=False,
        index=True,
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
