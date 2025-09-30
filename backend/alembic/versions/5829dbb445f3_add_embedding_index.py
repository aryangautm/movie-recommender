"""add_embedding_index

Revision ID: 5829dbb445f3
Revises: be68afef1585
Create Date: 2025-08-05 18:11:07.551435

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5829dbb445f3"
down_revision: Union[str, Sequence[str], None] = "be68afef1585"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if index exists before creating - makes migration idempotent
    connection = op.get_bind()
    result = connection.execute(
        sa.text(
            """
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'movies' AND indexname = 'ix_movies_embedding'
        """
        )
    ).fetchone()

    if not result:
        # For custom indexes like HNSW, using op.execute is the cleanest way
        op.execute(
            """
            CREATE INDEX ix_movies_embedding ON movies 
            USING hnsw (embedding vector_cosine_ops);
        """
        )


def downgrade() -> None:
    op.drop_index("ix_movies_embedding", table_name="movies")
