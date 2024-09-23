"""Create application table

Revision ID: 9a947cf59435
Revises: cd8f3f10f609
Create Date: 2024-08-15 19:50:30.415895

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a947cf59435'
down_revision = 'cd8f3f10f609'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('application',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('leave_start_date', sa.Date(), nullable=False),
    sa.Column('leave_end_date', sa.Date(), nullable=False),
    sa.Column('employee_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['employee_id'], ['employee.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('application')
    # ### end Alembic commands ###
