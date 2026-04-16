"""add preview_url to jobs

Revision ID: 4b1a2c3d4e5f
Revises: 0181138b9bb9
Create Date: 2026-04-16 10:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4b1a2c3d4e5f'
down_revision: str | Sequence[str] | None = '0181138b9bb9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('preview_url', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('jobs', schema=None) as batch_op:
        batch_op.drop_column('preview_url')
