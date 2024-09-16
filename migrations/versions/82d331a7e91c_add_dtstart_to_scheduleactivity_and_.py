"""Add dtstart to ScheduleActivity and adjust recurrence handling

Revision ID: 82d331a7e91c
Revises: 85e0a831b38c
Create Date: 2024-09-13 14:22:19.188727

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import DateTime

# revision identifiers, used by Alembic
revision = '82d331a7e91c'
down_revision = '85e0a831b38c'
branch_labels = None
depends_on = None

def upgrade():
    # Step 1: Add the column with a default value
    with op.batch_alter_table('schedule_activities', schema=None) as batch_op:
        batch_op.add_column(sa.Column('dtstart', sa.DateTime(), nullable=True))

    # Step 2: Populate the column with a sensible default value
    # For example, set all dtstart to '2024-01-01 00:00:00' for now
    op.execute("UPDATE schedule_activities SET dtstart = '2024-01-01 00:00:00' WHERE dtstart IS NULL")

    # Step 3: Alter the column to be non-nullable
    with op.batch_alter_table('schedule_activities', schema=None) as batch_op:
        batch_op.alter_column('dtstart', existing_type=sa.DateTime(), nullable=False)


def downgrade():
    with op.batch_alter_table('schedule_activities', schema=None) as batch_op:
        batch_op.drop_column('dtstart')

    # ### end Alembic commands ###
