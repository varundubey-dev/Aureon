"""add existing user id to pending signup

Revision ID: 3a3e5114b7ef
Revises: 3e4abf78a095
Create Date: 2026-05-20 02:38:27.907046

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3a3e5114b7ef"
down_revision: Union[str, Sequence[str], None] = "3e4abf78a095"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.add_column(
        "pending_signups",
        sa.Column(
            "existing_user_id",
            sa.UUID(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_pending_signups_existing_user_id",
        "pending_signups",
        "users",
        ["existing_user_id"],
        ["id"],
    )


def downgrade() -> None:

    op.drop_constraint(
        "fk_pending_signups_existing_user_id",
        "pending_signups",
        type_="foreignkey",
    )

    op.drop_column(
        "pending_signups",
        "existing_user_id",
    )