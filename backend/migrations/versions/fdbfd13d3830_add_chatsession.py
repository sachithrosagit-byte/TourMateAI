"""Add ChatSession

Revision ID: fdbfd13d3830
Revises: 277597e77299
Create Date: 2026-07-28 03:14:50.698391

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'fdbfd13d3830'
down_revision = '277597e77299'
branch_labels = None
depends_on = None


def upgrade():
    # Create ChatSessions table
    op.create_table('ChatSessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['Users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('ChatSessions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_ChatSessions_user_id'), ['user_id'], unique=False)

    # Add session_id to ChatLogs
    with op.batch_alter_table('ChatLogs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('session_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_ChatLogs_session_id'), ['session_id'], unique=False)
        batch_op.create_foreign_key('fk_chatlogs_session_id', 'ChatSessions', ['session_id'], ['id'], ondelete='CASCADE')


def downgrade():
    with op.batch_alter_table('ChatLogs', schema=None) as batch_op:
        batch_op.drop_constraint('fk_chatlogs_session_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_ChatLogs_session_id'))
        batch_op.drop_column('session_id')

    with op.batch_alter_table('ChatSessions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ChatSessions_user_id'))
    op.drop_table('ChatSessions')
