"""init

Revision ID: dba8170ea6a2
Revises: 
Create Date: 2025-07-09 10:24:04.416118

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'dba8170ea6a2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('api_logs',
                    sa.Column('method', sa.String(length=10), nullable=True),
                    sa.Column('url', sa.Text(), nullable=True),
                    sa.Column('request_headers', sa.Text(), nullable=True),
                    sa.Column('request_body', sa.Text(), nullable=True),
                    sa.Column('response_status', sa.Integer(), nullable=True),
                    sa.Column('response_headers', sa.Text(), nullable=True),
                    sa.Column('response_body', sa.Text(), nullable=True),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('dictionaries',
                    sa.Column('term', sa.Integer(), nullable=False),
                    sa.Column('definition', sa.String(), nullable=False),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_dictionaries_term'), 'dictionaries', ['term'], unique=False)
    op.create_table('global_config',
                    sa.Column('version', sa.Integer(), nullable=False),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('items',
                    sa.Column('code', sa.String(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.Column('is_product', sa.Boolean(), nullable=True),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('roles',
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)
    op.create_table('routes',
                    sa.Column('path', sa.String(), nullable=True),
                    sa.Column('method', sa.String(), nullable=True),
                    sa.Column('action', sa.String(), nullable=False),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_routes_path'), 'routes', ['path'], unique=False)
    op.create_table('tax_rates',
                    sa.Column('rate_id', sa.String(), nullable=False),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('rate', sa.Float(), nullable=False),
                    sa.Column('ordinal', sa.Integer(), nullable=True),
                    sa.Column('charge_mode', sa.String(), nullable=True),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('tenants',
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('code', sa.String(), nullable=False),
                    sa.Column('email', sa.String(), nullable=True),
                    sa.Column('phone_number', sa.String(), nullable=True),
                    sa.Column('tin', sa.String(), nullable=True),
                    sa.Column('config_version', sa.Integer(), nullable=True),
                    sa.Column('vat_registered', sa.Boolean(), nullable=True),
                    sa.Column('activated_tax_rate_ids', sa.JSON(), nullable=True),
                    sa.Column('tax_office_code', sa.String(), nullable=True),
                    sa.Column('tax_office_name', sa.String(), nullable=True),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_tenants_code'), 'tenants', ['code'], unique=True)
    op.create_index(op.f('ix_tenants_name'), 'tenants', ['name'], unique=True)
    op.create_table('products',
                    sa.Column('tenant_id', sa.UUID(), nullable=False),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('unit_price', sa.Float(), nullable=False),
                    sa.Column('quantity', sa.Integer(), nullable=False),
                    sa.Column('unit_of_measure', sa.String(), nullable=False),
                    sa.Column('site_id', sa.String(), nullable=True),
                    sa.Column('expiry_date', sa.DateTime(), nullable=True),
                    sa.Column('minimum_stock_level', sa.Integer(), nullable=True),
                    sa.Column('tax_rate_id', sa.String(), nullable=False),
                    sa.Column('is_product', sa.Boolean(), nullable=False),
                    sa.Column('code', sa.String(), nullable=False),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('profiles',
                    sa.Column('tenant_id', sa.UUID(), nullable=False),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('role_route_association',
                    sa.Column('role_id', sa.UUID(), nullable=False),
                    sa.Column('route_id', sa.UUID(), nullable=False),
                    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
                    sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ),
                    sa.PrimaryKeyConstraint('role_id', 'route_id')
                    )
    op.create_table('subscriptions',
                    sa.Column('tenant_id', sa.UUID(), nullable=True),
                    sa.Column('billing_cycle', sa.Enum('MONTHLY', 'ANNUAL', name='billingcycle'), nullable=True),
                    sa.Column('device_limit', sa.Integer(), nullable=True),
                    sa.Column('price', sa.Float(), nullable=True),
                    sa.Column('start_date', sa.DateTime(), nullable=True),
                    sa.Column('end_date', sa.DateTime(), nullable=True),
                    sa.Column('is_active', sa.Boolean(), nullable=True),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('terminals',
                    sa.Column('terminal_id', sa.String(), nullable=True),
                    sa.Column('secret_key', sa.String(), nullable=True),
                    sa.Column('token', sa.String(), nullable=True),
                    sa.Column('tenant_id', sa.UUID(), nullable=False),
                    sa.Column('confirmed_at', sa.DateTime(), nullable=True),
                    sa.Column('trading_name', sa.String(), nullable=True),
                    sa.Column('email', sa.String(), nullable=True),
                    sa.Column('phone_number', sa.String(), nullable=True),
                    sa.Column('label', sa.String(), nullable=True),
                    sa.Column('config_version', sa.Integer(), nullable=True),
                    sa.Column('address_lines', sa.JSON(), nullable=True),
                    sa.Column('offline_limit_hours', sa.Integer(), nullable=True),
                    sa.Column('offline_limit_amount', sa.Float(), nullable=True),
                    sa.Column('device_id', sa.String(), nullable=True),
                    sa.Column('activation_code', sa.String(), nullable=True),
                    sa.Column('site_id', sa.String(), nullable=False),
                    sa.Column('site_name', sa.String(), nullable=True),
                    sa.Column('is_blocked', sa.Boolean(), nullable=True),
                    sa.Column('blocking_reason', sa.String(), nullable=True),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('users',
                    sa.Column('email', sa.String(), nullable=True),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('phone_number', sa.String(), nullable=False),
                    sa.Column('hashed_password', sa.String(), nullable=True),
                    sa.Column('tenant_id', sa.UUID(), nullable=True),
                    sa.Column('role_id', sa.UUID(), nullable=True),
                    sa.Column('scope', sa.Integer(), nullable=True),
                    sa.Column('status', sa.Integer(), nullable=True),
                    sa.Column('last_login', sa.DateTime(), nullable=True),
                    sa.Column('last_logout', sa.DateTime(), nullable=True),
                    sa.Column('refresh_token_version', sa.Integer(), nullable=True),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
                    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('offline_transactions',
                    sa.Column('tenant_id', sa.UUID(), nullable=False),
                    sa.Column('terminal_id', sa.UUID(), nullable=False),
                    sa.Column('transaction_id', sa.String(), nullable=False),
                    sa.Column('details', sa.JSON(), nullable=False),
                    sa.Column('submitted_at', sa.DateTime(), nullable=True),
                    sa.Column('status', sa.String(), nullable=True),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
                    sa.ForeignKeyConstraint(['terminal_id'], ['terminals.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('payments',
                    sa.Column('subscription_id', sa.UUID(), nullable=True),
                    sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='paymentstatus'),
                              nullable=True),
                    sa.Column('proof_url', sa.String(), nullable=True),
                    sa.Column('uploaded_at', sa.DateTime(), nullable=True),
                    sa.Column('approved_at', sa.DateTime(), nullable=True),
                    sa.Column('admin_id', sa.UUID(), nullable=True),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=True),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('payments')
    op.drop_table('offline_transactions')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('terminals')
    op.drop_table('subscriptions')
    op.drop_table('role_route_association')
    op.drop_table('profiles')
    op.drop_table('products')
    op.drop_index(op.f('ix_tenants_name'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_code'), table_name='tenants')
    op.drop_table('tenants')
    op.drop_table('tax_rates')
    op.drop_index(op.f('ix_routes_path'), table_name='routes')
    op.drop_table('routes')
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_table('roles')
    op.drop_table('items')
    op.drop_table('global_config')
    op.drop_index(op.f('ix_dictionaries_term'), table_name='dictionaries')
    op.drop_table('dictionaries')
    op.drop_table('api_logs')
    # ### end Alembic commands ###
