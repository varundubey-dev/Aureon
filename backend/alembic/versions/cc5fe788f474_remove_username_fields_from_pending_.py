"""remove username fields from pending signups

Revision ID: cc5fe788f474
Revises: 184ddd40c3d3
Create Date: 2026-05-19 00:41:04.010935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc5fe788f474'
down_revision: Union[str, Sequence[str], None] = '184ddd40c3d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.drop_index(
        op.f('ix_pending_signups_username_normalized'),
        table_name='pending_signups',
    )

    op.drop_column(
        'pending_signups',
        'username_normalized',
    )

    op.drop_column(
        'pending_signups',
        'username',
    )


def downgrade() -> None:

    op.add_column(
        'pending_signups',
        sa.Column(
            'username',
            sa.String(),
            nullable=False,
            server_default='',
        )
    )

    op.add_column(
        'pending_signups',
        sa.Column(
            'username_normalized',
            sa.String(),
            nullable=False,
            server_default='',
        )
    )

    op.create_index(
        op.f('ix_pending_signups_username_normalized'),
        'pending_signups',
        ['username_normalized'],
        unique=False,
    )