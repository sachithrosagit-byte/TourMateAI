"""add ChatLogs.suggested_attractions

Stores the attraction ids a chatbot reply suggested so the Chat page can
re-render its inline attraction cards when history is reloaded.

Revision ID: 8d41f0c2b7a9
Revises: 963291c89037
Create Date: 2026-07-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d41f0c2b7a9'
down_revision = '963291c89037'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ChatLogs', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('suggested_attractions', sa.JSON(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table('ChatLogs', schema=None) as batch_op:
        batch_op.drop_column('suggested_attractions')
