"""add unique constraints for auth provider integrity

Revision ID: 9c0681235b2d
Revises: 3a3e5114b7ef
Create Date: 2026-05-20 17:13:32.716628

"""
from typing import Sequence, Union

from alembic import op


revision: str = "9c0681235b2d"
down_revision: Union[str, Sequence[str], None] = "3a3e5114b7ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_unique_constraint(
        "uq_user_provider",
        "auth_providers",
        [
            "user_id",
            "provider",
        ],
    )


def downgrade() -> None:

    op.drop_constraint(
        "uq_user_provider",
        "auth_providers",
        type_="unique",
    )