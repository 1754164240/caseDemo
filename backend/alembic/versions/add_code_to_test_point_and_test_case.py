"""add code to test_point and test_case

Revision ID: add_code_fields
Revises: 
Create Date: 2025-01-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_code_fields'
down_revision = None
head = None
branch_labels = None
depends_on = None


def upgrade():
    # 添加 code 字段到 test_points 表
    op.add_column('test_points', sa.Column('code', sa.String(length=20), nullable=True))
    
    # 添加 code 字段到 test_cases 表
    op.add_column('test_cases', sa.Column('code', sa.String(length=30), nullable=True))
    
    # 为现有数据生成编号
    connection = op.get_bind()
    
    # 生成测试点编号
    test_points = connection.execute(sa.text("SELECT id FROM test_points ORDER BY id")).fetchall()
    for idx, (tp_id,) in enumerate(test_points, start=1):
        code = f"TP-{idx:03d}"
        connection.execute(
            sa.text("UPDATE test_points SET code = :code WHERE id = :id"),
            {"code": code, "id": tp_id}
        )
    
    # 生成测试用例编号
    test_cases = connection.execute(
        sa.text("""
            SELECT tc.id, tp.code 
            FROM test_cases tc 
            JOIN test_points tp ON tc.test_point_id = tp.id 
            ORDER BY tc.test_point_id, tc.id
        """)
    ).fetchall()
    
    # 按测试点分组计数
    tp_counters = {}
    for tc_id, tp_code in test_cases:
        if tp_code not in tp_counters:
            tp_counters[tp_code] = 1
        else:
            tp_counters[tp_code] += 1
        
        code = f"{tp_code}-{tp_counters[tp_code]}"
        connection.execute(
            sa.text("UPDATE test_cases SET code = :code WHERE id = :id"),
            {"code": code, "id": tc_id}
        )
    
    # 创建唯一索引
    op.create_index('ix_test_points_code', 'test_points', ['code'], unique=True)
    op.create_index('ix_test_cases_code', 'test_cases', ['code'], unique=True)
    
    # 设置字段为非空
    op.alter_column('test_points', 'code', nullable=False)
    op.alter_column('test_cases', 'code', nullable=False)


def downgrade():
    # 删除索引
    op.drop_index('ix_test_cases_code', table_name='test_cases')
    op.drop_index('ix_test_points_code', table_name='test_points')
    
    # 删除字段
    op.drop_column('test_cases', 'code')
    op.drop_column('test_points', 'code')

