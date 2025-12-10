"""add period_end to ticker_stats

Revision ID: a8431237e25a
Revises: fda80b6a1a4f
Create Date: 2025-12-10 12:02:03.695073

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8431237e25a'
down_revision: Union[str, Sequence[str], None] = 'fda80b6a1a4f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ticker_stats",
        sa.Column("period_end", sa.Date(), nullable=False)
    )


def downgrade() -> None:
    op.drop_column("ticker_stats", "period_end")
