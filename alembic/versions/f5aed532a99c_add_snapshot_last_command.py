"""add_snapshot_last_command

Revision ID: f5aed532a99c
Revises: 23ff8deddb4a
Create Date: 2022-02-08 11:15:31.796081

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5aed532a99c'
down_revision = '23ff8deddb4a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('variant_study_snapshot', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_executed_command', sa.String(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('variant_study_snapshot', schema=None) as batch_op:
        batch_op.drop_column('last_executed_command')

    # ### end Alembic commands ###
