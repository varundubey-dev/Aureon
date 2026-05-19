"""make user identity fields nullable

Revision ID: 3e4abf78a095
Revises: cc5fe788f474
Create Date: 2026-05-20 01:48:59.134166

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3e4abf78a095"
down_revision: Union[str, Sequence[str], None] = "cc5fe788f474"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.alter_column(
        "users",
        "name",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )

    op.alter_column(
        "users",
        "username",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )

    op.alter_column(
        "users",
        "username_normalized",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )

    op.alter_column(
        "users",
        "email",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )


def downgrade() -> None:

    op.alter_column(
        "users",
        "email",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )

    op.alter_column(
        "users",
        "username_normalized",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )

    op.alter_column(
        "users",
        "username",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )

    op.alter_column(
        "users",
        "name",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )