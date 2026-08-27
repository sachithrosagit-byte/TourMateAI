"""Added Hotel model

Revision ID: 8fa5e60754f7
Revises: fdbfd13d3830
Create Date: 2026-07-29 02:14:32.398598

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '8fa5e60754f7'
down_revision = 'fdbfd13d3830'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('Hotels',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('location', sa.String(length=100), nullable=True),
    sa.Column('latitude', sa.Float(), nullable=True),
    sa.Column('longitude', sa.Float(), nullable=True),
    sa.Column('image_url', sa.String(length=500), nullable=True),
    sa.Column('avg_rating', sa.Float(), nullable=True),
    sa.Column('budget_tier', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('Hotels', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_Hotels_budget_tier'), ['budget_tier'], unique=False)
        batch_op.create_index(batch_op.f('ix_Hotels_location'), ['location'], unique=False)

    # Modify ItineraryItems to allow attraction_id to be nullable and add hotel_id
    with op.batch_alter_table('ItineraryItems', schema=None) as batch_op:
        batch_op.alter_column('attraction_id',
               existing_type=mysql.INTEGER(),
               nullable=True)
        batch_op.add_column(sa.Column('hotel_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_ItineraryItems_hotel_id'), ['hotel_id'], unique=False)
        batch_op.create_foreign_key(None, 'Hotels', ['hotel_id'], ['id'], ondelete='CASCADE')

def downgrade():
    with op.batch_alter_table('ItineraryItems', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_ItineraryItems_hotel_id'))
        batch_op.drop_column('hotel_id')
        batch_op.alter_column('attraction_id',
               existing_type=mysql.INTEGER(),
               nullable=False)

    with op.batch_alter_table('Hotels', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_Hotels_location'))
        batch_op.drop_index(batch_op.f('ix_Hotels_budget_tier'))
    op.drop_table('Hotels')
