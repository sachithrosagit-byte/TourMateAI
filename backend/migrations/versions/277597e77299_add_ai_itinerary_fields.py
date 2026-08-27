"""Add AI itinerary fields

Revision ID: 277597e77299
Revises: a7b3e9d24c10
Create Date: 2026-07-19 23:38:31.539442

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '277597e77299'
down_revision = 'a7b3e9d24c10'
branch_labels = None
depends_on = None

def upgrade():
    # Only add the columns for AI Planner
    with op.batch_alter_table('itineraries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_ai_generated', sa.Boolean(), nullable=True))

def downgrade():
    with op.batch_alter_table('itineraries', schema=None) as batch_op:
        batch_op.drop_column('is_ai_generated')
