"""boundaries and bi keys

Revision ID: a7c2e5d91f33
Revises: f4a1c7e92b06
Create Date: 2026-10-28 18:06:47.036290

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c2e5d91f33'
down_revision: Union[str, None] = 'f4a1c7e92b06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Postgres cannot drop enum values, so the audit values stay on downgrade (harmless).
    with op.get_context().autocommit_block():
        for v in ('BOUNDARY_CHANGE', 'API_KEY_CREATE', 'API_KEY_REVOKE'):
            op.execute(f"ALTER TYPE audit_action ADD VALUE IF NOT EXISTS '{v}'")
    op.create_table('admin_boundaries',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('level', sa.Enum('COUNTRY', 'STATE', 'LGA', 'WARD', 'FACILITY', name='boundary_level'), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('code', sa.String(length=40), nullable=True),
    sa.Column('parent_id', sa.UUID(), nullable=True),
    sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=True),
    sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['admin_boundaries.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_admin_boundaries_level_parent', 'admin_boundaries', ['level', 'parent_id'], unique=False)
    op.create_table('api_keys',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('key_prefix', sa.String(length=16), nullable=False),
    sa.Column('key_hash', sa.String(length=64), nullable=False),
    sa.Column('created_by', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)
    op.add_column('users', sa.Column('country_id', sa.UUID(), nullable=True))
    op.add_column('users', sa.Column('state_id', sa.UUID(), nullable=True))
    op.add_column('users', sa.Column('lga_id', sa.UUID(), nullable=True))
    op.add_column('users', sa.Column('ward_id', sa.UUID(), nullable=True))
    op.add_column('users', sa.Column('facility_id', sa.UUID(), nullable=True))
    op.add_column('users', sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=True))
    op.add_column('users', sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=True))
    op.create_index(op.f('ix_users_country_id'), 'users', ['country_id'], unique=False)
    op.create_index(op.f('ix_users_facility_id'), 'users', ['facility_id'], unique=False)
    op.create_index(op.f('ix_users_lga_id'), 'users', ['lga_id'], unique=False)
    op.create_index(op.f('ix_users_state_id'), 'users', ['state_id'], unique=False)
    op.create_index(op.f('ix_users_ward_id'), 'users', ['ward_id'], unique=False)
    op.create_foreign_key('fk_users_country_id', 'users', 'admin_boundaries', ['country_id'], ['id'])
    op.create_foreign_key('fk_users_lga_id', 'users', 'admin_boundaries', ['lga_id'], ['id'])
    op.create_foreign_key('fk_users_facility_id', 'users', 'admin_boundaries', ['facility_id'], ['id'])
    op.create_foreign_key('fk_users_ward_id', 'users', 'admin_boundaries', ['ward_id'], ['id'])
    op.create_foreign_key('fk_users_state_id', 'users', 'admin_boundaries', ['state_id'], ['id'])


def downgrade() -> None:
    for col in ('country', 'state', 'lga', 'ward', 'facility'):
        op.drop_constraint(f'fk_users_{col}_id', 'users', type_='foreignkey')
        op.drop_index(op.f(f'ix_users_{col}_id'), table_name='users')
        op.drop_column('users', f'{col}_id')
    op.drop_column('users', 'longitude')
    op.drop_column('users', 'latitude')
    op.drop_index(op.f('ix_api_keys_key_hash'), table_name='api_keys')
    op.drop_table('api_keys')
    op.drop_index('ix_admin_boundaries_level_parent', table_name='admin_boundaries')
    op.drop_table('admin_boundaries')
    op.execute('DROP TYPE IF EXISTS boundary_level')
