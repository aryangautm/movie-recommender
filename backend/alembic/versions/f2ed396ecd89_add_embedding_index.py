"""add embedding index

Revision ID: f2ed396ecd89
Revises: ff8091025c54
Create Date: 2025-08-05 01:52:12.729790

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f2ed396ecd89"
down_revision: Union[str, Sequence[str], None] = "ff8091025c54"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # For custom indexes like HNSW, using op.execute is the cleanest way
    op.execute(
        """
        CREATE INDEX ix_movies_embedding ON movies 
        USING hnsw (embedding vector_cosine_ops);
    """
    )


def downgrade() -> None:
    op.drop_index("ix_movies_embedding", table_name="movies")
