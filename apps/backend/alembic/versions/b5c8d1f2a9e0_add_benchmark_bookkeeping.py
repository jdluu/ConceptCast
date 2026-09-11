"""add benchmark bookkeeping columns

Revision ID: b5c8d1f2a9e0
Revises: ea7b3fa73d27
Create Date: 2026-09-11

Adds nullable benchmark-v2 bookkeeping columns to jobs:
  - benchmark_job_seq: manifest job_seq (exact join to manifest/jobs.csv)
  - benchmark_arm:     arm label (A=monolithic, B=monolithic+repair, C=council)
  - benchmark_rep:     replication index (1..n)

All nullable so non-benchmark (interactive/mock) usage is unaffected.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b5c8d1f2a9e0"
down_revision: str | Sequence[str] | None = "ea7b3fa73d27"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("benchmark_job_seq", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("benchmark_arm", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("benchmark_rep", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.drop_column("benchmark_rep")
        batch_op.drop_column("benchmark_arm")
        batch_op.drop_column("benchmark_job_seq")
