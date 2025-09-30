"""install_pgvector_extension

Revision ID: 111cf2b78ecd
Revises: 372f2f71ffc7
Create Date: 2025-09-30 13:34:41.785893

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "111cf2b78ecd"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Install pgvector extension if not already installed."""
    # Install pgvector extension - this is idempotent
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Remove pgvector extension."""
    # Note: In production, you might not want to drop the extension
    # as it could affect other databases using the same PostgreSQL instance
    op.execute("DROP EXTENSION IF EXISTS vector")
