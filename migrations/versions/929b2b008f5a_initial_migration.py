"""Initial migration

Revision ID: 929b2b008f5a
Revises: 
Create Date: 2024-09-13 12:58:52.571989

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '929b2b008f5a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('password_hash',
               existing_type=sa.VARCHAR(length=128),
               type_=sa.String(length=512),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('password_hash',
               existing_type=sa.String(length=512),
               type_=sa.VARCHAR(length=128),
               existing_nullable=False)

    # ### end Alembic commands ###
