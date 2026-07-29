"""multi tenancy: site_id on brands

Revision ID: 9a4d2e6f7c31
Revises: 3c7e9f21a5b2
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a4d2e6f7c31'
down_revision: Union[str, None] = '3c7e9f21a5b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CHEMISTO_SITE_ID = "11111111-1111-1111-1111-111111111111"


def upgrade() -> None:
    op.add_column('brands', sa.Column('site_id', sa.UUID(), nullable=True))
    op.execute(f"UPDATE brands SET site_id = '{CHEMISTO_SITE_ID}' WHERE site_id IS NULL")
    op.alter_column('brands', 'site_id', nullable=False)
    op.create_index(op.f('ix_brands_site_id'), 'brands', ['site_id'], unique=False)
    op.create_foreign_key(
        'fk_brands_site_id_sites', 'brands', 'sites', ['site_id'], ['id'], ondelete='CASCADE'
    )

    op.drop_index('ix_brands_name', table_name='brands')
    op.create_index(op.f('ix_brands_name'), 'brands', ['name'], unique=False)
    op.drop_index('ix_brands_slug', table_name='brands')
    op.create_index(op.f('ix_brands_slug'), 'brands', ['slug'], unique=False)
    op.create_unique_constraint('uq_brands_site_id_name', 'brands', ['site_id', 'name'])
    op.create_unique_constraint('uq_brands_site_id_slug', 'brands', ['site_id', 'slug'])


def downgrade() -> None:
    op.drop_constraint('uq_brands_site_id_slug', 'brands', type_='unique')
    op.drop_constraint('uq_brands_site_id_name', 'brands', type_='unique')
    op.drop_index(op.f('ix_brands_slug'), table_name='brands')
    op.create_index('ix_brands_slug', 'brands', ['slug'], unique=True)
    op.drop_index(op.f('ix_brands_name'), table_name='brands')
    op.create_index('ix_brands_name', 'brands', ['name'], unique=True)

    op.drop_constraint('fk_brands_site_id_sites', 'brands', type_='foreignkey')
    op.drop_index(op.f('ix_brands_site_id'), table_name='brands')
    op.drop_column('brands', 'site_id')
