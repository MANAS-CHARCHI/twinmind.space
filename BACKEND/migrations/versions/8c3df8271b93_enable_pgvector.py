"""enable_pgvector

Revision ID: 8c3df8271b93
Revises: d666dac2eab7
Create Date: 2026-02-25 16:56:15.491374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector


# revision identifiers, used by Alembic.
revision: str = '8c3df8271b93'
down_revision: Union[str, Sequence[str], None] = 'd666dac2eab7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
