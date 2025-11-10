"""add business_line to test_point

Revision ID: add_business_line
Revises: add_code_to_test_point_and_test_case
Create Date: 2025-01-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_business_line'
down_revision = 'add_code_to_test_point_and_test_case'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 business_line 字段到 test_points 表
    op.add_column('test_points', sa.Column('business_line', sa.String(length=50), nullable=True))


def downgrade():
    # 删除 business_line 字段
    op.drop_column('test_points', 'business_line')

