"""Create send records tables

Revision ID: f1a2b3c4d5e6
Revises: 05e79d53b42e
Create Date: 2024-07-29 16:50:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'f1a2b3c4d5e6'
down_revision = '05e79d53b42e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create batch_send_records table
    op.create_table('batch_send_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_name', sa.String(length=255), nullable=True),
        sa.Column('total_count', sa.Integer(), nullable=False),
        sa.Column('success_count', sa.Integer(), nullable=False),
        sa.Column('failed_count', sa.Integer(), nullable=False),
        sa.Column('pending_count', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('batch_id')
    )
    
    # Create message_send_records table
    op.create_table('message_send_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('recipient_id', sa.String(length=255), nullable=False),
        sa.Column('recipient_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['batch_id'], ['batch_send_records.batch_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_batch_send_records_batch_id', 'batch_send_records', ['batch_id'])
    op.create_index('idx_batch_send_records_status', 'batch_send_records', ['status'])
    op.create_index('idx_batch_send_records_created_at', 'batch_send_records', ['created_at'])
    
    op.create_index('idx_message_send_records_batch_id', 'message_send_records', ['batch_id'])
    op.create_index('idx_message_send_records_status', 'message_send_records', ['status'])
    op.create_index('idx_message_send_records_channel', 'message_send_records', ['channel'])
    op.create_index('idx_message_send_records_created_at', 'message_send_records', ['created_at'])
    
    # Create composite indexes
    op.create_index('idx_message_batch_status', 'message_send_records', ['batch_id', 'status'])
    op.create_index('idx_message_channel_status', 'message_send_records', ['channel', 'status'])
    op.create_index('idx_message_channel_created_at', 'message_send_records', ['channel', 'created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_message_channel_created_at', table_name='message_send_records')
    op.drop_index('idx_message_channel_status', table_name='message_send_records')
    op.drop_index('idx_message_batch_status', table_name='message_send_records')
    op.drop_index('idx_message_send_records_created_at', table_name='message_send_records')
    op.drop_index('idx_message_send_records_channel', table_name='message_send_records')
    op.drop_index('idx_message_send_records_status', table_name='message_send_records')
    op.drop_index('idx_message_send_records_batch_id', table_name='message_send_records')
    
    op.drop_index('idx_batch_send_records_created_at', table_name='batch_send_records')
    op.drop_index('idx_batch_send_records_status', table_name='batch_send_records')
    op.drop_index('idx_batch_send_records_batch_id', table_name='batch_send_records')
    
    # Drop tables
    op.drop_table('message_send_records')
    op.drop_table('batch_send_records')