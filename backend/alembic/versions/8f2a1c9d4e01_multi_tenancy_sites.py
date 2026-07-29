"""multi tenancy: sites, site_id on products and users

Revision ID: 8f2a1c9d4e01
Revises: 6b48524ad691
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union
import uuid
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = '8f2a1c9d4e01'
down_revision: Union[str, None] = '6b48524ad691'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed IDs (not random) so this migration is deterministic and safe to
# re-read/re-run against, and so the two seeded sites always have the same
# UUID no matter which environment it runs in.
CHEMISTO_SITE_ID = "11111111-1111-1111-1111-111111111111"
CHEMISTO_FOOD_SITE_ID = "22222222-2222-2222-2222-222222222222"


def upgrade() -> None:
    # 1) Create the sites table.
    op.create_table(
        'sites',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('slug', sa.String(length=80), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sites_id'), 'sites', ['id'], unique=False)
    op.create_index(op.f('ix_sites_slug'), 'sites', ['slug'], unique=True)

    # 2) Seed the two known sites.
    sites_table = table(
        'sites',
        column('id', sa.UUID()),
        column('slug', sa.String()),
        column('name', sa.String()),
        column('created_at', sa.DateTime(timezone=True)),
    )
    op.bulk_insert(
        sites_table,
        [
            {
                'id': uuid.UUID(CHEMISTO_SITE_ID),
                'slug': 'chemisto',
                'name': 'Chemisto',
                'created_at': datetime.now(timezone.utc),
            },
            {
                'id': uuid.UUID(CHEMISTO_FOOD_SITE_ID),
                'slug': 'chemisto-food',
                'name': 'Chemisto Food',
                'created_at': datetime.now(timezone.utc),
            },
        ],
    )

    # 3) Add site_id to products: nullable first, backfill, then lock down.
    op.add_column('products', sa.Column('site_id', sa.UUID(), nullable=True))
    op.execute(f"UPDATE products SET site_id = '{CHEMISTO_SITE_ID}' WHERE site_id IS NULL")
    op.alter_column('products', 'site_id', nullable=False)
    op.create_index(op.f('ix_products_site_id'), 'products', ['site_id'], unique=False)
    op.create_foreign_key(
        'fk_products_site_id_sites', 'products', 'sites', ['site_id'], ['id'], ondelete='CASCADE'
    )

    # 4) Add site_id to users: nullable first, backfill, then lock down.
    op.add_column('users', sa.Column('site_id', sa.UUID(), nullable=True))
    op.execute(f"UPDATE users SET site_id = '{CHEMISTO_SITE_ID}' WHERE site_id IS NULL")
    op.alter_column('users', 'site_id', nullable=False)
    op.create_index(op.f('ix_users_site_id'), 'users', ['site_id'], unique=False)
    op.create_foreign_key(
        'fk_users_site_id_sites', 'users', 'sites', ['site_id'], ['id'], ondelete='CASCADE'
    )

    # 5) Replace the old global-unique index on users.email with a
    #    composite unique(site_id, email), since the same email may now
    #    register separately on each site.
    op.drop_index('ix_users_email', table_name='users')
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_unique_constraint('uq_users_site_id_email', 'users', ['site_id', 'email'])


def downgrade() -> None:
    op.drop_constraint('uq_users_site_id_email', 'users', type_='unique')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.drop_constraint('fk_users_site_id_sites', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_site_id'), table_name='users')
    op.drop_column('users', 'site_id')

    op.drop_constraint('fk_products_site_id_sites', 'products', type_='foreignkey')
    op.drop_index(op.f('ix_products_site_id'), table_name='products')
    op.drop_column('products', 'site_id')

    op.drop_index(op.f('ix_sites_slug'), table_name='sites')
    op.drop_index(op.f('ix_sites_id'), table_name='sites')
    op.drop_table('sites')
