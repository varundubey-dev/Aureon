import uuid

from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import SQLModel, Field


class RefreshSession(SQLModel, table=True):
    __tablename__: str = "refresh_sessions"

    id: UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
    )

    user_id: UUID = Field(
        foreign_key="users.id",
        nullable=False,
        index=True,
    )

    token_hash: str = Field(nullable=False)

    expires_at: datetime = Field(nullable=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
