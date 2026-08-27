"""add Users.is_admin

Boolean admin flag gating the /api/admin/* endpoints. Existing rows default to
non-admin; flip a user with `flask set-admin <email>`.

Revision ID: c4f8a2d61e35
Revises: 8d41f0c2b7a9
Create Date: 2026-07-07

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4f8a2d61e35'
down_revision = '8d41f0c2b7a9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('Users', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'is_admin',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('0'),
            )
        )


def downgrade():
    with op.batch_alter_table('Users', schema=None) as batch_op:
        batch_op.drop_column('is_admin')
