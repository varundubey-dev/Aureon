"""add verified field to otp codes

Revision ID: c00d8c568bf2
Revises: 6a4002377ef1
Create Date: 2026-05-18 23:00:31.090749

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c00d8c568bf2'
down_revision: Union[str, Sequence[str], None] = '6a4002377ef1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'otp_codes',
        sa.Column(
            'verified',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        )
    )


def downgrade() -> None:
    op.drop_column(
        'otp_codes',
        'verified',
    )