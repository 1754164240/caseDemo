"""
测试文档处理功能
"""
import os
from app.services.document_parser import DocumentParser
from app.services.ai_service import ai_service
from app.core.config import settings

def test_document_parsing():
    """测试文档解析"""
    print("=" * 60)
    print("测试文档解析功能")
    print("=" * 60)
    print()
    
    # 创建测试文本文件
    test_file = "test_requirement.txt"
    test_content = """
保险产品需求文档

1. 产品创建功能
   - 用户可以创建新的保险产品
   - 需要填写产品名称、类型、保费等信息
   - 系统自动生成产品编号

2. 保费计算功能
   - 根据年龄、性别、保额计算保费
   - 支持多种计算规则
   - 计算结果需要精确到小数点后两位

3. 保单管理功能
   - 查看保单列表
   - 修改保单信息
   - 删除保单
"""
    
    try:
        # 写入测试文件
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"✅ 创建测试文件: {test_file}")
        print()
        
        # 测试解析
        print("测试文档解析...")
        text = DocumentParser.parse(test_file, 'txt')
        
        if text:
            print(f"✅ 文档解析成功")
            print(f"   文本长度: {len(text)} 字符")
            print()
            print("解析内容预览:")
            print("-" * 60)
            print(text[:200] + "..." if len(text) > 200 else text)
            print("-" * 60)
            print()
        else:
            print("❌ 文档解析失败")
            return
        
        # 测试 AI 提取
        print("测试 AI 测试点提取...")
        print()
        
        # 检查 API Key
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "":
            print("⚠️  OpenAI API Key 未配置")
            print("   将使用模拟数据")
            print()
            print("配置方法:")
            print("   1. 编辑 backend/.env 文件")
            print("   2. 设置 OPENAI_API_KEY=你的API密钥")
            print()
        else:
            print(f"✅ OpenAI API Key 已配置")
            print(f"   API Base: {settings.OPENAI_API_BASE}")
            print(f"   Model: {settings.MODEL_NAME}")
            print()
        
        try:
            test_points = ai_service.extract_test_points(text)
            
            print(f"✅ 测试点提取成功")
            print(f"   提取到 {len(test_points)} 个测试点")
            print()
            
            print("测试点列表:")
            print("-" * 60)
            for i, tp in enumerate(test_points, 1):
                print(f"{i}. {tp.get('title', 'N/A')}")
                print(f"   描述: {tp.get('description', 'N/A')}")
                print(f"   分类: {tp.get('category', 'N/A')}")
                print(f"   优先级: {tp.get('priority', 'N/A')}")
                print()
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ 测试点提取失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
    finally:
        # 清理测试文件
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"🗑️  删除测试文件: {test_file}")
    
    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)


def test_openai_connection():
    """测试 OpenAI 连接"""
    print("=" * 60)
    print("测试 OpenAI API 连接")
    print("=" * 60)
    print()
    
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "":
        print("❌ OpenAI API Key 未配置")
        print()
        print("请配置 OpenAI API Key:")
        print("   1. 编辑 backend/.env 文件")
        print("   2. 添加: OPENAI_API_KEY=sk-your-api-key-here")
        print()
        return
    
    print(f"API Key: {settings.OPENAI_API_KEY[:20]}...")
    print(f"API Base: {settings.OPENAI_API_BASE}")
    print(f"Model: {settings.MODEL_NAME}")
    print()
    
    try:
        print("发送测试请求...")
        from langchain_openai import ChatOpenAI
        
        llm = ChatOpenAI(
            model=settings.MODEL_NAME,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE if settings.OPENAI_API_BASE else None,
            temperature=0.7
        )
        
        response = llm.invoke("Hello, this is a test. Please respond with 'OK'.")
        print(f"✅ OpenAI API 连接成功")
        print(f"   响应: {response.content}")
        print()
        
    except Exception as e:
        print(f"❌ OpenAI API 连接失败: {str(e)}")
        print()
        print("可能的原因:")
        print("   1. API Key 无效")
        print("   2. 网络连接问题")
        print("   3. API Base URL 配置错误")
        print()
        import traceback
        traceback.print_exc()
    
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        test_openai_connection()
    else:
        test_document_parsing()
        print()
        print("提示: 运行 'python -m scripts.test_document_processing api' 测试 OpenAI API 连接")
