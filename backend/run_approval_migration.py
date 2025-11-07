"""
执行审批功能数据库迁移
"""
import psycopg
from app.core.config import settings

def run_migration():
    """执行迁移脚本"""
    # 从 DATABASE_URL 中提取连接信息
    # DATABASE_URL 格式: postgresql+psycopg://user:password@host:port/dbname
    database_url = settings.DATABASE_URL
    # 移除 +psycopg 部分，psycopg 库使用 postgresql:// 格式
    conn_str = database_url.replace('postgresql+psycopg://', 'postgresql://')

    print("连接数据库...")
    print(f"连接字符串: {conn_str.split('@')[0]}@***")
    
    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                print("\n开始执行迁移脚本...")
                
                # 读取迁移脚本
                with open('migrations/002_add_approval_fields.sql', 'r', encoding='utf-8') as f:
                    sql = f.read()
                
                # 执行迁移
                cur.execute(sql)
                conn.commit()
                
                print("✅ 迁移脚本执行成功!")
                
                # 验证迁移结果
                print("\n验证迁移结果...")
                
                # 检查测试点表的新字段
                cur.execute("""
                    SELECT column_name, data_type, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'test_points'
                    AND column_name IN ('approval_status', 'approved_by', 'approved_at', 'approval_comment')
                    ORDER BY column_name
                """)
                
                print("\n测试点表新增字段:")
                for row in cur.fetchall():
                    print(f"  - {row[0]}: {row[1]} (默认值: {row[2]})")
                
                # 检查测试用例表的新字段
                cur.execute("""
                    SELECT column_name, data_type, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'test_cases'
                    AND column_name IN ('approval_status', 'approved_by', 'approved_at', 'approval_comment')
                    ORDER BY column_name
                """)
                
                print("\n测试用例表新增字段:")
                for row in cur.fetchall():
                    print(f"  - {row[0]}: {row[1]} (默认值: {row[2]})")
                
                # 检查索引
                cur.execute("""
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename IN ('test_points', 'test_cases')
                    AND indexname LIKE '%approval%'
                    ORDER BY indexname
                """)
                
                print("\n新增索引:")
                for row in cur.fetchall():
                    print(f"  - {row[0]}")
                
                # 统计数据
                cur.execute("SELECT COUNT(*) FROM test_points")
                test_points_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM test_cases")
                test_cases_count = cur.fetchone()[0]
                
                print(f"\n数据统计:")
                print(f"  - 测试点总数: {test_points_count}")
                print(f"  - 测试用例总数: {test_cases_count}")
                
                print("\n✅ 迁移验证完成!")
                
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()

