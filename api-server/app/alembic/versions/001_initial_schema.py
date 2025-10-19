"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    tenant_status = postgresql.ENUM('active', 'suspended', 'deleted', name='tenantstatus')
    tenant_status.create(op.get_bind())
    
    billing_mode = postgresql.ENUM('postpaid', 'prepaid', name='billingmode')
    billing_mode.create(op.get_bind())
    
    did_status = postgresql.ENUM('free', 'assigned', 'reserved', name='didstatus')
    did_status.create(op.get_bind())
    
    user_role = postgresql.ENUM('superadmin', 'tenant_admin', 'manager', 'agent', name='userrole')
    user_role.create(op.get_bind())
    
    api_user_role = postgresql.ENUM('whmcs', 'admin', 'system', name='apiuserrole')
    api_user_role.create(op.get_bind())

    # plan_templates table
    op.create_table('plan_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('limits_json', postgresql.JSON(astext_type=sa.Text()), server_default='{}'),
        sa.Column('routing_json', postgresql.JSON(astext_type=sa.Text()), server_default='{}'),
        sa.Column('propagate_updates', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )

    # tenants table
    op.create_table('tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), unique=True, nullable=False),
        sa.Column('status', sa.Enum('active', 'suspended', 'deleted', name='tenantstatus'), server_default='active', nullable=False),
        sa.Column('limits_json', postgresql.JSON(astext_type=sa.Text()), server_default='{}'),
        sa.Column('billing_mode', sa.Enum('postpaid', 'prepaid', name='billingmode'), server_default='postpaid'),
        sa.Column('plan_template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('plan_templates.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()')),
    )

    # extensions table
    op.create_table('extensions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('secret_hash', sa.String(length=255), nullable=False),
        sa.Column('webrtc', sa.Boolean(), server_default='true'),
        sa.Column('forwarding_json', postgresql.JSON(astext_type=sa.Text()), server_default='{}'),
        sa.Column('voicemail_email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_index('idx_extensions_username', 'extensions', ['username'])

    # dids table
    op.create_table('dids',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('e164', sa.String(length=20), unique=True, nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=True),
        sa.Column('status', sa.Enum('free', 'assigned', 'reserved', name='didstatus'), server_default='free', nullable=False),
        sa.Column('routing_json', postgresql.JSON(astext_type=sa.Text()), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_index('idx_dids_e164', 'dids', ['e164'])

    # trunks table
    op.create_table('trunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('host', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('secret', sa.String(length=255), nullable=True),
        sa.Column('priority', sa.Integer(), server_default='100'),
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )

    # cdr table
    op.create_table('cdr',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('src', sa.String(length=100), nullable=False),
        sa.Column('dst', sa.String(length=100), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('billsec', sa.Integer(), server_default='0'),
        sa.Column('disposition', sa.String(length=50), nullable=True),
        sa.Column('trunk_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('trunks.id'), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_index('idx_cdr_started_at', 'cdr', ['started_at'])

    # recordings table
    op.create_table('recordings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('call_id', sa.String(length=255), nullable=False),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('duration', sa.Integer(), server_default='0'),
        sa.Column('size_bytes', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_index('idx_recordings_created_at', 'recordings', ['created_at'])

    # ivr_trees table
    op.create_table('ivr_trees',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('json', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )

    # usage_snapshots table
    op.create_table('usage_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('from_ts', sa.DateTime(), nullable=False),
        sa.Column('to_ts', sa.DateTime(), nullable=False),
        sa.Column('minutes_in', sa.Integer(), server_default='0'),
        sa.Column('minutes_out', sa.Integer(), server_default='0'),
        sa.Column('storage_gb', sa.Float(), server_default='0'),
        sa.Column('sms_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_index('idx_usage_snapshots_created_at', 'usage_snapshots', ['created_at'])

    # api_users table
    op.create_table('api_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(length=100), unique=True, nullable=False),
        sa.Column('secret_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('whmcs', 'admin', 'system', name='apiuserrole'), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_index('idx_api_users_username', 'api_users', ['username'])

    # portal_users table
    op.create_table('portal_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=True),
        sa.Column('email', sa.String(length=255), unique=True, nullable=False),
        sa.Column('pass_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('superadmin', 'tenant_admin', 'manager', 'agent', name='userrole'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_index('idx_portal_users_email', 'portal_users', ['email'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('portal_users')
    op.drop_table('api_users')
    op.drop_table('usage_snapshots')
    op.drop_table('ivr_trees')
    op.drop_table('recordings')
    op.drop_table('cdr')
    op.drop_table('trunks')
    op.drop_table('dids')
    op.drop_table('extensions')
    op.drop_table('tenants')
    op.drop_table('plan_templates')
    
    # Drop enums
    sa.Enum(name='apiuserrole').drop(op.get_bind())
    sa.Enum(name='userrole').drop(op.get_bind())
    sa.Enum(name='didstatus').drop(op.get_bind())
    sa.Enum(name='billingmode').drop(op.get_bind())
    sa.Enum(name='tenantstatus').drop(op.get_bind())
