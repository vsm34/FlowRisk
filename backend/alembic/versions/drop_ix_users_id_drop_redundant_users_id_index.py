"""drop redundant users.id index

Revision ID: drop_ix_users_id
Revises: 21baeb513acf
Create Date: 2026-01-07

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'drop_ix_users_id'
down_revision: Union[str, None] = '21baeb513acf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop redundant index on id (primary keys are already indexed)
    op.drop_index(op.f('ix_users_id'), table_name='users')


def downgrade() -> None:
    # Recreate index if rolling back
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
