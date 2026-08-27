"""add admin-portal moderation columns + AdminActions

Backs the expanded admin portal:
  - Feedback.is_hidden      — moderation flag for public reviews
  - ChatLogs.quality_flag   — admin marks a bot reply "unhelpful"/"incorrect"
  - AdminActions            — audit trail (e.g. retraining requests)

Revision ID: a7b3e9d24c10
Revises: c4f8a2d61e35
Create Date: 2026-07-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7b3e9d24c10'
down_revision = 'c4f8a2d61e35'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('Feedback', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'is_hidden',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('0'),
            )
        )

    with op.batch_alter_table('ChatLogs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('quality_flag', sa.String(length=20), nullable=True))
        batch_op.create_index(
            batch_op.f('ix_ChatLogs_quality_flag'), ['quality_flag'], unique=False
        )

    op.create_table(
        'AdminActions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['Users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('AdminActions', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_AdminActions_admin_id'), ['admin_id'], unique=False
        )
        batch_op.create_index(
            batch_op.f('ix_AdminActions_action_type'), ['action_type'], unique=False
        )


def downgrade():
    with op.batch_alter_table('AdminActions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_AdminActions_action_type'))
        batch_op.drop_index(batch_op.f('ix_AdminActions_admin_id'))
    op.drop_table('AdminActions')

    with op.batch_alter_table('ChatLogs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_ChatLogs_quality_flag'))
        batch_op.drop_column('quality_flag')

    with op.batch_alter_table('Feedback', schema=None) as batch_op:
        batch_op.drop_column('is_hidden')
