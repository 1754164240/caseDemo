"""数据库迁移脚本，执行 SQL 迁移文件。"""
from sqlalchemy import create_engine, text

from app.core.config import settings
from scripts import MIGRATIONS_DIR


def run_migration(sql_file: str):
    """执行 SQL 迁移文件"""
    print(f"开始执行迁移 {sql_file}")

    engine = create_engine(settings.DATABASE_URL)

    sql_path = MIGRATIONS_DIR / sql_file
    if not sql_path.exists():
        print(f"错误: 找不到迁移文件 {sql_path}")
        return False

    sql_content = sql_path.read_text(encoding="utf-8")

    try:
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                statements = []
                current_statement = []
                in_do_block = False

                for line in sql_content.split('\n'):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('--'):
                        continue

                    current_statement.append(line)

                    if 'DO $$' in line or 'DO $' in line:
                        in_do_block = True

                    if in_do_block and 'END $$;' in line:
                        in_do_block = False
                        statements.append('\n'.join(current_statement))
                        current_statement = []
                    elif not in_do_block and ';' in line:
                        statements.append('\n'.join(current_statement))
                        current_statement = []

                for i, stmt in enumerate(statements, 1):
                    if not stmt.strip():
                        continue
                    print(f"执行语句 {i}/{len(statements)}...")
                    result = conn.execute(text(stmt))

                    if stmt.strip().upper().startswith('SELECT'):
                        try:
                            rows = result.fetchall()
                            if rows:
                                for row in rows:
                                    print(f"  {dict(row._mapping)}")
                        except Exception:
                            pass

                trans.commit()
                print("✅迁移成功完成!")
                return True

            except Exception as exc:
                trans.rollback()
                print(f"迁移失败: {exc}")
                import traceback

                traceback.print_exc()
                raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    run_migration("001_add_code_fields.sql")
