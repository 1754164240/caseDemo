"""
数据库迁移脚本
执行 SQL 迁移文件
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


def run_migration(sql_file: str):
    """执行 SQL 迁移文件"""
    print(f"开始执行迁移: {sql_file}")
    
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL)
    
    # 读取 SQL 文件
    sql_path = Path(__file__).parent / "migrations" / sql_file
    if not sql_path.exists():
        print(f"错误: 找不到迁移文件 {sql_path}")
        return False
    
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 执行 SQL
    try:
        with engine.connect() as conn:
            # 开启事务
            trans = conn.begin()
            try:
                # 分割 SQL 语句（按 DO $$ ... END $$; 和普通语句分割）
                statements = []
                current_statement = []
                in_do_block = False
                
                for line in sql_content.split('\n'):
                    # 跳过注释和空行
                    stripped = line.strip()
                    if not stripped or stripped.startswith('--'):
                        continue
                    
                    current_statement.append(line)
                    
                    # 检测 DO 块
                    if 'DO $$' in line or 'DO $' in line:
                        in_do_block = True
                    
                    # 检测 DO 块结束
                    if in_do_block and 'END $$;' in line:
                        in_do_block = False
                        statements.append('\n'.join(current_statement))
                        current_statement = []
                    # 普通语句以分号结束
                    elif not in_do_block and ';' in line:
                        statements.append('\n'.join(current_statement))
                        current_statement = []
                
                # 执行每个语句
                for i, stmt in enumerate(statements, 1):
                    if stmt.strip():
                        print(f"执行语句 {i}/{len(statements)}...")
                        result = conn.execute(text(stmt))
                        
                        # 如果是 SELECT 语句，打印结果
                        if stmt.strip().upper().startswith('SELECT'):
                            try:
                                rows = result.fetchall()
                                if rows:
                                    for row in rows:
                                        print(f"  {dict(row._mapping)}")
                            except:
                                pass
                
                # 提交事务
                trans.commit()
                print("✅ 迁移成功完成!")
                return True
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"❌ 迁移失败: {str(e)}")
                import traceback
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("数据库迁移工具")
    print("=" * 60)
    
    # 执行迁移
    success = run_migration("001_add_code_fields.sql")
    
    if success:
        print("\n" + "=" * 60)
        print("迁移完成! 现在可以启动应用程序。")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("迁移失败! 请检查错误信息。")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

