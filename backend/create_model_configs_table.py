"""
创建 model_configs 表并迁移现有配置的脚本
"""
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings


def create_model_configs_table():
    """创建 model_configs 表并迁移现有配置"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("步骤 1: 创建 model_configs 表...")
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS model_configs (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL,
        display_name VARCHAR(200) NOT NULL,
        description TEXT,
        api_key TEXT NOT NULL,
        api_base VARCHAR(500) NOT NULL,
        model_name VARCHAR(200) NOT NULL,
        temperature VARCHAR(10) DEFAULT '0.7',
        max_tokens INTEGER,
        provider VARCHAR(50),
        model_type VARCHAR(50) DEFAULT 'chat',
        is_active BOOLEAN DEFAULT TRUE,
        is_default BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE
    );
    
    CREATE INDEX IF NOT EXISTS idx_model_configs_name ON model_configs(name);
    CREATE INDEX IF NOT EXISTS idx_model_configs_is_default ON model_configs(is_default);
    """
    
    try:
        with engine.connect() as conn:
            # 创建表
            conn.execute(text(create_table_sql))
            conn.commit()
            print("✅ model_configs 表创建成功")
            
            # 检查表是否存在
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'model_configs'
            """))
            
            if not result.fetchone():
                print("❌ 表验证失败")
                sys.exit(1)
            
            print("✅ 表验证成功")
            
            # 步骤 2: 从 system_configs 迁移现有配置
            print("\n步骤 2: 检查并迁移现有模型配置...")
            
            # 检查是否已有配置
            existing_count = conn.execute(text("SELECT COUNT(*) FROM model_configs")).scalar()
            
            if existing_count > 0:
                print(f"⚠️  已存在 {existing_count} 个模型配置,跳过迁移")
            else:
                # 从 system_configs 读取现有配置
                api_key_result = conn.execute(text("""
                    SELECT config_value FROM system_configs 
                    WHERE config_key = 'OPENAI_API_KEY'
                """))
                api_key_row = api_key_result.fetchone()
                api_key = api_key_row[0] if api_key_row else ""
                
                api_base_result = conn.execute(text("""
                    SELECT config_value FROM system_configs 
                    WHERE config_key = 'OPENAI_API_BASE'
                """))
                api_base_row = api_base_result.fetchone()
                api_base = api_base_row[0] if api_base_row else "https://api.openai.com/v1"
                
                model_name_result = conn.execute(text("""
                    SELECT config_value FROM system_configs 
                    WHERE config_key = 'MODEL_NAME'
                """))
                model_name_row = model_name_result.fetchone()
                model_name = model_name_row[0] if model_name_row else "gpt-4"
                
                if api_key or api_base or model_name:
                    # 插入默认配置
                    conn.execute(text("""
                        INSERT INTO model_configs 
                        (name, display_name, description, api_key, api_base, model_name, 
                         provider, is_active, is_default)
                        VALUES 
                        (:name, :display_name, :description, :api_key, :api_base, :model_name,
                         :provider, :is_active, :is_default)
                    """), {
                        "name": "default",
                        "display_name": "默认模型配置",
                        "description": "从系统配置迁移的默认模型",
                        "api_key": api_key,
                        "api_base": api_base,
                        "model_name": model_name,
                        "provider": "openai",
                        "is_active": True,
                        "is_default": True
                    })
                    conn.commit()
                    print("✅ 已迁移现有配置为默认模型")
                    print(f"   - API Base: {api_base}")
                    print(f"   - Model Name: {model_name}")
                else:
                    print("⚠️  未找到现有配置,跳过迁移")
            
            # 步骤 3: 显示当前配置
            print("\n步骤 3: 当前模型配置列表:")
            result = conn.execute(text("""
                SELECT id, name, display_name, model_name, is_default, is_active
                FROM model_configs
                ORDER BY is_default DESC, id
            """))
            
            configs = result.fetchall()
            if configs:
                print("\n{:<5} {:<20} {:<30} {:<30} {:<10} {:<10}".format(
                    "ID", "Name", "Display Name", "Model Name", "Default", "Active"
                ))
                print("-" * 115)
                for config in configs:
                    print("{:<5} {:<20} {:<30} {:<30} {:<10} {:<10}".format(
                        config[0], config[1], config[2], config[3],
                        "是" if config[4] else "否",
                        "是" if config[5] else "否"
                    ))
            else:
                print("   (无配置)")
                
    except Exception as e:
        print(f"❌ 操作失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    print("=" * 80)
    print("创建 model_configs 表并迁移现有配置")
    print("=" * 80)
    print()
    
    create_model_configs_table()
    
    print()
    print("=" * 80)
    print("完成")
    print("=" * 80)

