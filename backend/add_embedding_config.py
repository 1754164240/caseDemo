"""
添加 Embedding 模型配置
"""
from app.db.session import SessionLocal
from app.models.system_config import SystemConfig

def add_embedding_config():
    """添加 Embedding 模型配置"""
    db = SessionLocal()
    
    try:
        # ModelScope 支持的中文 embedding 模型
        # 参考: https://modelscope.cn/models
        embedding_model = "BAAI/bge-small-zh-v1.5"
        
        # 检查是否已存在
        existing = db.query(SystemConfig).filter(
            SystemConfig.config_key == 'EMBEDDING_MODEL'
        ).first()
        
        if existing:
            print(f"⚠️  配置已存在: {existing.config_value}")
            print(f"更新为: {embedding_model}")
            existing.config_value = embedding_model
            existing.description = "Embedding 模型 (ModelScope 支持的中文 embedding 模型)"
        else:
            print(f"添加新配置: {embedding_model}")
            config = SystemConfig(
                config_key='EMBEDDING_MODEL',
                config_value=embedding_model,
                description='Embedding 模型 (ModelScope 支持的中文 embedding 模型)'
            )
            db.add(config)
        
        db.commit()
        print(f"✅ Embedding 模型配置已保存: {embedding_model}")
        
        # 显示所有模型配置
        print("\n当前所有模型配置:")
        configs = db.query(SystemConfig).filter(
            SystemConfig.config_key.in_(['OPENAI_API_KEY', 'OPENAI_API_BASE', 'MODEL_NAME', 'EMBEDDING_MODEL'])
        ).all()
        
        for c in configs:
            value = c.config_value
            if c.config_key == 'OPENAI_API_KEY':
                value = value[:20] + '...' if len(value) > 20 else value
            print(f"  {c.config_key}: {value}")
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_embedding_config()

