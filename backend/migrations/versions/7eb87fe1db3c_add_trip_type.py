"""add trip_type

Revision ID: 7eb87fe1db3c
Revises: 8fa5e60754f7
Create Date: 2026-08-13 20:19:49.247203

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '7eb87fe1db3c'
down_revision = '8fa5e60754f7'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('Itineraries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('trip_type', sa.String(length=50), nullable=True, server_default='Solo'))

def downgrade():
    with op.batch_alter_table('Itineraries', schema=None) as batch_op:
        batch_op.drop_column('trip_type')
