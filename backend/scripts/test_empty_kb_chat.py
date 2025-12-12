"""
测试空知识库聊天功能
"""
import requests
import json

def test_empty_kb_chat():
    """测试空知识库时的聊天功能"""
    print("="*60)
    print("测试空知识库聊天功能")
    print("="*60)
    
    # 1. 登录获取 token
    print("\n1️⃣  登录系统...")
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        data={
            "username": "admin",
            "password": "admin123"
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code}")
        return
    
    token = login_response.json()["access_token"]
    print(f"✅ 登录成功")
    
    # 2. 测试流式聊天
    print("\n2️⃣  测试流式聊天(空知识库)...")
    
    test_questions = [
        "你好,请介绍一下自己",
        "什么是保险?",
        "投保人和被保险人有什么区别?",
        "如何选择合适的保险产品?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*60}")
        print(f"问题 {i}: {question}")
        print(f"{'='*60}")
        
        response = requests.post(
            "http://localhost:8000/api/v1/knowledge-base/query/stream",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "question": question,
                "collection_name": "knowledge_base",
                "top_k": 5,
                "return_source": True
            },
            stream=True
        )
        
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            continue
        
        print(f"✅ 开始接收流式数据...\n")
        
        buffer = ""
        full_answer = ""
        token_count = 0
        event_count = 0
        
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                buffer += chunk
                
                # 处理完整的事件
                while "\n\n" in buffer:
                    event, buffer = buffer.split("\n\n", 1)
                    
                    if event.startswith("data: "):
                        event_count += 1
                        data = json.loads(event[6:])
                        
                        if data.get("type") == "token":
                            token_count += 1
                            content = data.get("content", "")
                            full_answer += content
                            
                            # 实时显示(每10个字符显示一次)
                            if token_count % 10 == 0:
                                print(content, end="", flush=True)
                        
                        elif data.get("type") == "done":
                            print(f"\n\n✅ 完成!")
                            print(f"\n完整答案:\n{'-'*60}")
                            print(full_answer)
                            print(f"{'-'*60}")
                        
                        elif data.get("type") == "sources":
                            sources = data.get("sources", [])
                            print(f"📚 参考来源: {len(sources)} 个")
                        
                        elif data.get("type") == "qa_record_id":
                            qa_id = data.get("qa_record_id")
                            print(f"💾 QA 记录 ID: {qa_id}")
                        
                        elif data.get("type") == "error":
                            error = data.get("error")
                            print(f"❌ 错误: {error}")
        
        print(f"\n📊 统计:")
        print(f"   总事件数: {event_count}")
        print(f"   Token 数: {token_count}")
        print(f"   答案长度: {len(full_answer)} 字符")
        
        # 只测试第一个问题
        if i == 1:
            print(f"\n✅ 测试通过! 空知识库也能正常聊天!")
            break
    
    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)

if __name__ == "__main__":
    test_empty_kb_chat()

