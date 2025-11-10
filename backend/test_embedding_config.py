"""
测试 Embedding 配置功能
"""
from app.db.session import SessionLocal
from app.models.system_config import SystemConfig

def test_embedding_config():
    """测试 Embedding 配置"""
    print("="*60)
    print("测试 Embedding 配置功能")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # 1. 查看当前配置
        print("\n1️⃣  当前配置:")
        configs = db.query(SystemConfig).filter(
            SystemConfig.config_key.in_([
                'OPENAI_API_KEY', 'OPENAI_API_BASE', 'MODEL_NAME',
                'EMBEDDING_MODEL', 'EMBEDDING_API_KEY', 'EMBEDDING_API_BASE'
            ])
        ).all()
        
        config_dict = {c.config_key: c.config_value for c in configs}
        
        print(f"\nLLM 配置:")
        print(f"  OPENAI_API_KEY: {config_dict.get('OPENAI_API_KEY', 'N/A')[:20]}...")
        print(f"  OPENAI_API_BASE: {config_dict.get('OPENAI_API_BASE', 'N/A')}")
        print(f"  MODEL_NAME: {config_dict.get('MODEL_NAME', 'N/A')}")
        
        print(f"\nEmbedding 配置:")
        print(f"  EMBEDDING_MODEL: {config_dict.get('EMBEDDING_MODEL', 'N/A')}")
        print(f"  EMBEDDING_API_KEY: {config_dict.get('EMBEDDING_API_KEY', 'N/A')[:20] if config_dict.get('EMBEDDING_API_KEY') else '(空,使用 LLM 的 API Key)'}...")
        print(f"  EMBEDDING_API_BASE: {config_dict.get('EMBEDDING_API_BASE', 'N/A') or '(空,使用 LLM 的 API Base)'}")
        
        # 2. 测试 RAG 服务初始化
        print("\n2️⃣  测试 RAG 服务初始化:")
        from app.services.rag_service import RAGService
        
        rag_service = RAGService(db)
        
        print(f"\n✅ RAG 服务初始化成功!")
        print(f"\nLLM 配置:")
        print(f"  Model: {rag_service.llm.model_name}")
        print(f"  API Base: {rag_service.llm.openai_api_base}")
        
        print(f"\nEmbedding 配置:")
        print(f"  Model: {rag_service.embeddings.model}")
        print(f"  API Base: {rag_service.embeddings.openai_api_base}")
        
        # 3. 验证配置逻辑
        print("\n3️⃣  验证配置逻辑:")
        
        embedding_api_key = config_dict.get('EMBEDDING_API_KEY', '')
        embedding_api_base = config_dict.get('EMBEDDING_API_BASE', '')
        llm_api_key = config_dict.get('OPENAI_API_KEY', '')
        llm_api_base = config_dict.get('OPENAI_API_BASE', '')
        
        if not embedding_api_key:
            print(f"  ✅ Embedding API Key 为空,使用 LLM 的 API Key")
        else:
            print(f"  ✅ Embedding 使用单独的 API Key")
        
        if not embedding_api_base:
            print(f"  ✅ Embedding API Base 为空,使用 LLM 的 API Base")
        else:
            print(f"  ✅ Embedding 使用单独的 API Base: {embedding_api_base}")
        
        # 4. 配置建议
        print("\n4️⃣  配置建议:")
        print("\n场景 1: LLM 和 Embedding 使用同一个服务")
        print("  - 只需配置 LLM 的 API Key 和 API Base")
        print("  - Embedding API Key 和 API Base 留空")
        print("  - 例如: 都使用 ModelScope")
        
        print("\n场景 2: LLM 和 Embedding 使用不同服务")
        print("  - LLM 配置: ModelScope (DeepSeek-V3.1)")
        print("  - Embedding 配置: OpenAI (text-embedding-ada-002)")
        print("  - 需要单独配置 Embedding 的 API Key 和 API Base")
        
        print("\n场景 3: 使用本地 Embedding 模型")
        print("  - LLM 配置: ModelScope")
        print("  - Embedding 配置: 本地服务 (如 Ollama)")
        print("  - Embedding API Base: http://localhost:11434/v1")
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)

if __name__ == "__main__":
    test_embedding_config()

