"""
测试 RAG 服务配置
"""
from app.db.session import SessionLocal
from app.services.rag_service import RAGService

def test_rag_config():
    """测试 RAG 服务配置"""
    print("="*60)
    print("测试 RAG 服务配置")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # 创建 RAG 服务
        print("\n创建 RAG 服务...")
        rag_service = RAGService(db)
        
        print("\n✅ RAG 服务创建成功!")
        print(f"\nLLM 配置:")
        print(f"  Model: {rag_service.llm.model_name}")
        print(f"  API Base: {rag_service.llm.openai_api_base}")
        
        print(f"\nEmbedding 配置:")
        print(f"  Model: {rag_service.embeddings.model}")
        print(f"  API Base: {rag_service.embeddings.openai_api_base}")
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_rag_config()

