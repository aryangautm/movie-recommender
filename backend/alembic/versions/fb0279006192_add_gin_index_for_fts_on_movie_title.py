"""Add GIN index for FTS on movie title

Revision ID: fb0279006192
Revises: 3e179e7c8630
Create Date: 2025-08-01 22:17:27.582303

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fb0279006192"
down_revision: Union[str, Sequence[str], None] = "3e179e7c8630"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            """
            CREATE INDEX CONCURRENTLY idx_movie_title_fts 
            ON movies 
            USING GIN (to_tsvector('english', title));
        """
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY idx_movie_title_fts;")
