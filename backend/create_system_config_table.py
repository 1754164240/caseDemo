"""
创建 system_configs 表的脚本
"""
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

def create_system_config_table():
    """创建 system_configs 表"""
    engine = create_engine(settings.DATABASE_URL)
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS system_configs (
        id SERIAL PRIMARY KEY,
        config_key VARCHAR(100) UNIQUE NOT NULL,
        config_value TEXT NOT NULL,
        description VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE
    );
    
    CREATE INDEX IF NOT EXISTS idx_system_configs_key ON system_configs(config_key);
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
            print("✅ system_configs 表创建成功")
            
            # 检查表是否存在
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'system_configs'
            """))
            
            if result.fetchone():
                print("✅ 表验证成功")
            else:
                print("❌ 表验证失败")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ 创建表失败: {str(e)}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("=" * 60)
    print("创建 system_configs 表")
    print("=" * 60)
    print()
    
    create_system_config_table()
    
    print()
    print("=" * 60)
    print("完成")
    print("=" * 60)

