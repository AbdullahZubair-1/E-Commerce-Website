"""superadmin: nullable site_id on users, is_superadmin flag

Revision ID: 5b1e8a3c9d47
Revises: 9a4d2e6f7c31
Create Date: 2026-07-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b1e8a3c9d47'
down_revision: Union[str, None] = '9a4d2e6f7c31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # A superadmin account belongs to no single site.
    op.alter_column('users', 'site_id', nullable=True)

    op.add_column(
        'users',
        sa.Column('is_superadmin', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # Drop the server_default after backfilling existing rows -- new rows
    # will always specify it explicitly at the application level.
    op.alter_column('users', 'is_superadmin', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'is_superadmin')
    op.execute("UPDATE users SET site_id = '11111111-1111-1111-1111-111111111111' WHERE site_id IS NULL")
    op.alter_column('users', 'site_id', nullable=False)