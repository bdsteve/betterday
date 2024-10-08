"""Increase recurrence field length

Revision ID: 85e0a831b38c
Revises: 929b2b008f5a
Create Date: 2024-09-13 13:40:03.398297

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '85e0a831b38c'
down_revision = '929b2b008f5a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('schedule_activities', schema=None) as batch_op:
        batch_op.alter_column('recurrence',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=200),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('schedule_activities', schema=None) as batch_op:
        batch_op.alter_column('recurrence',
               existing_type=sa.String(length=200),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)

    # ### end Alembic commands ###
