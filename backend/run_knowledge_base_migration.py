"""
执行知识库数据库迁移
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings


def run_migration():
    """执行知识库迁移"""
    print("=" * 60)
    print("执行知识库数据库迁移")
    print("=" * 60)
    
    # 创建数据库连接
    engine = create_engine(str(settings.DATABASE_URL))
    
    try:
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                # 读取 SQL 文件
                sql_file = os.path.join(os.path.dirname(__file__), "migrations", "004_add_knowledge_base.sql")
                
                print(f"\n1. 读取 SQL 文件: {sql_file}")
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # 分割 SQL 语句
                sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                
                print(f"   ✅ 找到 {len(sql_statements)} 条 SQL 语句")
                
                # 执行 SQL 语句
                print("\n2. 执行 SQL 语句...")
                for i, stmt in enumerate(sql_statements, 1):
                    if stmt.strip():
                        print(f"   执行语句 {i}/{len(sql_statements)}...")
                        conn.execute(text(stmt))
                
                print("   ✅ 所有 SQL 语句执行成功")
                
                # 验证表是否创建成功
                print("\n3. 验证表创建...")
                
                # 检查 knowledge_documents 表
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'knowledge_documents'
                    ORDER BY ordinal_position
                """))
                
                columns = result.fetchall()
                if columns:
                    print(f"   ✅ knowledge_documents 表创建成功 ({len(columns)} 个字段)")
                    for col in columns[:5]:  # 显示前5个字段
                        print(f"      - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
                    if len(columns) > 5:
                        print(f"      ... 还有 {len(columns) - 5} 个字段")
                else:
                    print("   ❌ knowledge_documents 表创建失败")
                    trans.rollback()
                    return
                
                # 检查 qa_records 表
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'qa_records'
                    ORDER BY ordinal_position
                """))
                
                columns = result.fetchall()
                if columns:
                    print(f"   ✅ qa_records 表创建成功 ({len(columns)} 个字段)")
                    for col in columns[:5]:  # 显示前5个字段
                        print(f"      - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
                    if len(columns) > 5:
                        print(f"      ... 还有 {len(columns) - 5} 个字段")
                else:
                    print("   ❌ qa_records 表创建失败")
                    trans.rollback()
                    return
                
                # 提交事务
                trans.commit()
                
                print("\n" + "=" * 60)
                print("✅ 迁移成功完成!")
                print("=" * 60)
                print("\n说明:")
                print("- knowledge_documents 表已创建 (知识库文档)")
                print("- qa_records 表已创建 (问答记录)")
                print("- 所有索引和外键已创建")
                print("\n现在可以使用知识库功能了!")
                
            except Exception as e:
                trans.rollback()
                print(f"\n❌ 迁移失败: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
                
    except Exception as e:
        print(f"\n❌ 数据库连接失败: {str(e)}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"\n执行失败: {str(e)}")
        sys.exit(1)

