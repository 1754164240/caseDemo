"""
验证数据库迁移结果
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


def verify_migration():
    """验证迁移结果"""
    print("=" * 60)
    print("验证数据库迁移结果")
    print("=" * 60)
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # 检查测试点编号
        print("\n1. 测试点编号检查:")
        print("-" * 60)
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(code) as with_code,
                COUNT(DISTINCT code) as unique_codes
            FROM test_points
        """))
        row = result.fetchone()
        print(f"   总测试点数: {row[0]}")
        print(f"   有编号的: {row[1]}")
        print(f"   唯一编号数: {row[2]}")
        
        if row[0] == row[1] == row[2]:
            print("   ✅ 所有测试点都有唯一编号")
        else:
            print("   ❌ 存在问题：编号不完整或有重复")
        
        # 显示测试点编号示例
        print("\n   测试点编号示例:")
        result = conn.execute(text("""
            SELECT code, title 
            FROM test_points 
            ORDER BY code 
            LIMIT 5
        """))
        for row in result:
            print(f"   - {row[0]}: {row[1]}")
        
        # 检查测试用例编号
        print("\n2. 测试用例编号检查:")
        print("-" * 60)
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(code) as with_code,
                COUNT(DISTINCT code) as unique_codes
            FROM test_cases
        """))
        row = result.fetchone()
        print(f"   总测试用例数: {row[0]}")
        print(f"   有编号的: {row[1]}")
        print(f"   唯一编号数: {row[2]}")
        
        if row[0] == row[1] == row[2]:
            print("   ✅ 所有测试用例都有唯一编号")
        else:
            print("   ❌ 存在问题：编号不完整或有重复")
        
        # 显示测试用例编号示例
        print("\n   测试用例编号示例:")
        result = conn.execute(text("""
            SELECT tc.code, tc.title, tp.code as test_point_code
            FROM test_cases tc
            JOIN test_points tp ON tc.test_point_id = tp.id
            ORDER BY tc.code 
            LIMIT 5
        """))
        for row in result:
            print(f"   - {row[0]} (测试点: {row[2]}): {row[1]}")
        
        # 检查编号格式
        print("\n3. 编号格式检查:")
        print("-" * 60)
        
        # 检查测试点编号格式
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM test_points 
            WHERE code !~ '^TP-[0-9]{3}$'
        """))
        invalid_tp = result.scalar()
        if invalid_tp == 0:
            print("   ✅ 所有测试点编号格式正确 (TP-XXX)")
        else:
            print(f"   ❌ 有 {invalid_tp} 个测试点编号格式不正确")
        
        # 检查测试用例编号格式
        result = conn.execute(text("""
            SELECT COUNT(*) 
            FROM test_cases 
            WHERE code !~ '^TP-[0-9]{3}-[0-9]+$'
        """))
        invalid_tc = result.scalar()
        if invalid_tc == 0:
            print("   ✅ 所有测试用例编号格式正确 (TP-XXX-Y)")
        else:
            print(f"   ❌ 有 {invalid_tc} 个测试用例编号格式不正确")
        
        # 检查索引
        print("\n4. 索引检查:")
        print("-" * 60)
        result = conn.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename IN ('test_points', 'test_cases')
            AND indexname LIKE '%code%'
        """))
        indexes = [row[0] for row in result]
        
        if 'ix_test_points_code' in indexes:
            print("   ✅ test_points.code 索引已创建")
        else:
            print("   ❌ test_points.code 索引缺失")
        
        if 'ix_test_cases_code' in indexes:
            print("   ✅ test_cases.code 索引已创建")
        else:
            print("   ❌ test_cases.code 索引缺失")
        
        # 检查字段约束
        print("\n5. 字段约束检查:")
        print("-" * 60)
        result = conn.execute(text("""
            SELECT 
                column_name,
                is_nullable,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'test_points' AND column_name = 'code'
        """))
        row = result.fetchone()
        if row:
            print(f"   test_points.code:")
            print(f"   - 可为空: {row[1]}")
            print(f"   - 最大长度: {row[2]}")
            if row[1] == 'NO':
                print("   ✅ 字段设置为非空")
            else:
                print("   ⚠️  字段允许为空")
        
        result = conn.execute(text("""
            SELECT 
                column_name,
                is_nullable,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'test_cases' AND column_name = 'code'
        """))
        row = result.fetchone()
        if row:
            print(f"\n   test_cases.code:")
            print(f"   - 可为空: {row[1]}")
            print(f"   - 最大长度: {row[2]}")
            if row[1] == 'NO':
                print("   ✅ 字段设置为非空")
            else:
                print("   ⚠️  字段允许为空")
    
    print("\n" + "=" * 60)
    print("验证完成!")
    print("=" * 60)


if __name__ == "__main__":
    verify_migration()
