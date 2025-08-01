"""added metadata to movies

Revision ID: 3e179e7c8630
Revises: d8bf7c7c18cc
Create Date: 2025-07-31 17:46:21.235796

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e179e7c8630'
down_revision: Union[str, Sequence[str], None] = 'd8bf7c7c18cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('movies', sa.Column('keywords', sa.JSON(), nullable=True))
    op.add_column('movies', sa.Column('director', sa.JSON(), nullable=True))
    op.add_column('movies', sa.Column('cast', sa.JSON(), nullable=True))
    op.add_column('movies', sa.Column('collection', sa.JSON(), nullable=True))
    op.add_column('movies', sa.Column('vote_count', sa.Integer(), nullable=True))
    op.add_column('movies', sa.Column('vote_average', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('movies', 'vote_average')
    op.drop_column('movies', 'vote_count')
    op.drop_column('movies', 'collection')
    op.drop_column('movies', 'cast')
    op.drop_column('movies', 'director')
    op.drop_column('movies', 'keywords')
    # ### end Alembic commands ###
