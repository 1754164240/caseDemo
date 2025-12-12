"""
检查测试点的 business_line 字段
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


def main():
    print("=" * 70)
    print("检查测试点的 business_line 字段")
    print("=" * 70)
    
    try:
        # 创建数据库连接
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # 1. 统计 business_line 字段情况
            print("\n1. 统计 business_line 字段情况...")
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN business_line IS NULL OR business_line = '' THEN 1 END) as empty_count,
                    COUNT(CASE WHEN business_line IS NOT NULL AND business_line != '' THEN 1 END) as filled_count
                FROM test_points
            """))
            
            row = result.fetchone()
            print(f"   总测试点数: {row[0]}")
            print(f"   business_line 为空: {row[1]}")
            print(f"   business_line 有值: {row[2]}")
            
            # 2. 查看最近的测试点
            print("\n2. 查看最近创建的 10 个测试点...")
            result = conn.execute(text("""
                SELECT id, code, title, business_line, created_at
                FROM test_points
                ORDER BY created_at DESC
                LIMIT 10
            """))
            
            print(f"\n{'ID':<6} {'编号':<12} {'业务线':<20} {'标题':<30}")
            print("-" * 70)
            for row in result:
                test_point_id = row[0]
                code = row[1]
                title = row[2][:28] if row[2] else ''
                business_line = row[3] if row[3] else '(空)'
                print(f"{test_point_id:<6} {code:<12} {business_line:<20} {title:<30}")
            
            # 3. 按业务线分组统计
            print("\n3. 按业务线分组统计...")
            result = conn.execute(text("""
                SELECT 
                    CASE 
                        WHEN business_line IS NULL OR business_line = '' THEN '(空)'
                        ELSE business_line
                    END as bl,
                    COUNT(*) as count
                FROM test_points
                GROUP BY bl
                ORDER BY count DESC
            """))
            
            print(f"\n{'业务线':<30} {'数量':<10}")
            print("-" * 40)
            for row in result:
                print(f"{row[0]:<30} {row[1]:<10}")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
