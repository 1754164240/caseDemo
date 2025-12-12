"""
测试 LangChain Short-term Memory (对话历史) 功能
"""
import requests
import json

# 配置
API_BASE = "http://localhost:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin123"

def login():
    """登录获取 token"""
    response = requests.post(
        f"{API_BASE}/auth/login",
        data={
            "username": USERNAME,
            "password": PASSWORD
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ 登录成功")
        return token
    else:
        print(f"❌ 登录失败: {response.text}")
        return None

def test_conversation_with_memory(token):
    """测试带对话历史的多轮对话"""
    print("\n" + "="*60)
    print("测试 Short-term Memory (对话历史)")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 对话历史
    chat_history = []
    
    # 第一轮对话
    print("\n【第 1 轮对话】")
    question1 = "什么是保险?"
    print(f"用户: {question1}")
    
    response = requests.post(
        f"{API_BASE}/knowledge-base/query",
        headers=headers,
        json={
            "question": question1,
            "collection_name": "knowledge_base",
            "top_k": 5,
            "return_source": True,
            "chat_history": chat_history
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        answer1 = result.get("answer", "")
        print(f"AI: {answer1[:200]}...")
        
        # 添加到对话历史
        chat_history.append({"role": "user", "content": question1})
        chat_history.append({"role": "assistant", "content": answer1})
    else:
        print(f"❌ 查询失败: {response.text}")
        return
    
    # 第二轮对话 (引用上一轮)
    print("\n【第 2 轮对话】")
    question2 = "它有哪些类型?"  # "它" 指代 "保险"
    print(f"用户: {question2}")
    print(f"💡 提示: 这个问题引用了上一轮对话中的 '保险'")
    
    response = requests.post(
        f"{API_BASE}/knowledge-base/query",
        headers=headers,
        json={
            "question": question2,
            "collection_name": "knowledge_base",
            "top_k": 5,
            "return_source": True,
            "chat_history": chat_history  # 传递对话历史
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        answer2 = result.get("answer", "")
        print(f"AI: {answer2[:200]}...")
        
        # 添加到对话历史
        chat_history.append({"role": "user", "content": question2})
        chat_history.append({"role": "assistant", "content": answer2})
    else:
        print(f"❌ 查询失败: {response.text}")
        return
    
    # 第三轮对话 (继续引用)
    print("\n【第 3 轮对话】")
    question3 = "第一种类型的特点是什么?"  # 引用第二轮的回答
    print(f"用户: {question3}")
    print(f"💡 提示: 这个问题引用了上一轮对话中提到的类型")
    
    response = requests.post(
        f"{API_BASE}/knowledge-base/query",
        headers=headers,
        json={
            "question": question3,
            "collection_name": "knowledge_base",
            "top_k": 5,
            "return_source": True,
            "chat_history": chat_history  # 传递对话历史
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        answer3 = result.get("answer", "")
        print(f"AI: {answer3[:200]}...")
    else:
        print(f"❌ 查询失败: {response.text}")
        return
    
    # 显示完整对话历史
    print("\n" + "="*60)
    print("完整对话历史:")
    print("="*60)
    for i, msg in enumerate(chat_history):
        role = "用户" if msg["role"] == "user" else "AI"
        content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
        print(f"\n[{i+1}] {role}: {content}")
    
    print("\n" + "="*60)
    print("✅ 测试完成!")
    print("="*60)
    print("\n💡 关键点:")
    print("1. 第 2 轮对话中的 '它' 能正确理解为 '保险'")
    print("2. 第 3 轮对话能理解 '第一种类型' 指的是什么")
    print("3. AI 能基于对话历史理解上下文关系")

def test_conversation_without_memory(token):
    """测试不带对话历史的对话 (对比)"""
    print("\n" + "="*60)
    print("对比测试: 不使用对话历史")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 第一轮对话
    print("\n【第 1 轮对话】")
    question1 = "什么是保险?"
    print(f"用户: {question1}")
    
    response = requests.post(
        f"{API_BASE}/knowledge-base/query",
        headers=headers,
        json={
            "question": question1,
            "collection_name": "knowledge_base",
            "top_k": 5,
            "return_source": True
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        answer1 = result.get("answer", "")
        print(f"AI: {answer1[:200]}...")
    else:
        print(f"❌ 查询失败: {response.text}")
        return
    
    # 第二轮对话 (不传递历史)
    print("\n【第 2 轮对话】")
    question2 = "它有哪些类型?"  # "它" 指代不明
    print(f"用户: {question2}")
    print(f"💡 提示: 不传递对话历史,AI 无法理解 '它' 指什么")
    
    response = requests.post(
        f"{API_BASE}/knowledge-base/query",
        headers=headers,
        json={
            "question": question2,
            "collection_name": "knowledge_base",
            "top_k": 5,
            "return_source": True
            # 不传递 chat_history
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        answer2 = result.get("answer", "")
        print(f"AI: {answer2[:200]}...")
        print(f"\n❌ 预期结果: AI 无法理解 '它' 指什么,回答可能不准确")
    else:
        print(f"❌ 查询失败: {response.text}")

if __name__ == "__main__":
    # 登录
    token = login()
    if not token:
        exit(1)
    
    # 测试带对话历史的对话
    test_conversation_with_memory(token)
    
    # 对比测试: 不带对话历史
    test_conversation_without_memory(token)

