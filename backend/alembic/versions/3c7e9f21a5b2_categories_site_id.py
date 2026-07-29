"""multi tenancy: site_id on categories

Revision ID: 3c7e9f21a5b2
Revises: 8f2a1c9d4e01
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c7e9f21a5b2'
down_revision: Union[str, None] = '8f2a1c9d4e01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CHEMISTO_SITE_ID = "11111111-1111-1111-1111-111111111111"


def upgrade() -> None:
    # 1) Add site_id: nullable first, backfill existing categories to
    #    Chemisto (since they were all created before multi-tenancy existed),
    #    then lock it down.
    op.add_column('categories', sa.Column('site_id', sa.UUID(), nullable=True))
    op.execute(f"UPDATE categories SET site_id = '{CHEMISTO_SITE_ID}' WHERE site_id IS NULL")
    op.alter_column('categories', 'site_id', nullable=False)
    op.create_index(op.f('ix_categories_site_id'), 'categories', ['site_id'], unique=False)
    op.create_foreign_key(
        'fk_categories_site_id_sites', 'categories', 'sites', ['site_id'], ['id'], ondelete='CASCADE'
    )

    # 2) Replace the old global-unique indexes on name/slug with composite
    #    unique(site_id, name) / unique(site_id, slug), since each site can
    #    now have its own "Lab Consumables", etc. without clashing.
    op.drop_index('ix_categories_name', table_name='categories')
    op.create_index(op.f('ix_categories_name'), 'categories', ['name'], unique=False)
    op.drop_index('ix_categories_slug', table_name='categories')
    op.create_index(op.f('ix_categories_slug'), 'categories', ['slug'], unique=False)
    op.create_unique_constraint('uq_categories_site_id_name', 'categories', ['site_id', 'name'])
    op.create_unique_constraint('uq_categories_site_id_slug', 'categories', ['site_id', 'slug'])


def downgrade() -> None:
    op.drop_constraint('uq_categories_site_id_slug', 'categories', type_='unique')
    op.drop_constraint('uq_categories_site_id_name', 'categories', type_='unique')
    op.drop_index(op.f('ix_categories_slug'), table_name='categories')
    op.create_index('ix_categories_slug', 'categories', ['slug'], unique=True)
    op.drop_index(op.f('ix_categories_name'), table_name='categories')
    op.create_index('ix_categories_name', 'categories', ['name'], unique=True)

    op.drop_constraint('fk_categories_site_id_sites', 'categories', type_='foreignkey')
    op.drop_index(op.f('ix_categories_site_id'), table_name='categories')
    op.drop_column('categories', 'site_id')
