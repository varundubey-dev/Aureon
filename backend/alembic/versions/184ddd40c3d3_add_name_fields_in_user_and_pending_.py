"""add name fields in user and pending_signups

Revision ID: 184ddd40c3d3
Revises: c00d8c568bf2
Create Date: 2026-05-19 00:18:43.547444

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '184ddd40c3d3'
down_revision: Union[str, Sequence[str], None] = 'c00d8c568bf2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'pending_signups',
        sa.Column(
            'name',
            sa.String(),
            nullable=False,
            server_default='',
        )
    )

    op.add_column(
        'users',
        sa.Column(
            'name',
            sa.String(),
            nullable=False,
            server_default='',
        )
    )


def downgrade() -> None:
    op.drop_column(
        'users',
        'name',
    )

    op.drop_column(
        'pending_signups',
        'name',
    )