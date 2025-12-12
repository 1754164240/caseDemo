"""
详细测试流式 API
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login():
    """登录获取 token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ 登录成功")
        return token
    else:
        print(f"❌ 登录失败: {response.status_code}")
        print(response.text)
        return None

def test_streaming(token):
    """测试流式 API"""
    print("\n" + "="*60)
    print("测试流式 API")
    print("="*60)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "question": "你好,请介绍一下自己",
        "collection_name": "knowledge_base",
        "top_k": 5,
        "return_source": True
    }
    
    print(f"\n📤 发送请求:")
    print(f"   问题: {data['question']}")
    print(f"   集合: {data['collection_name']}")
    
    response = requests.post(
        f"{BASE_URL}/knowledge-base/query/stream",
        headers=headers,
        json=data,
        stream=True
    )
    
    print(f"\n📥 响应状态: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ 请求失败")
        print(f"响应内容: {response.text}")
        return
    
    print(f"✅ 开始接收流式数据...\n")
    print("-"*60)
    
    event_count = 0
    token_count = 0
    full_answer = ""
    
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            
            if line_str.startswith('data: '):
                event_count += 1
                data_str = line_str[6:]
                
                try:
                    data = json.loads(data_str)
                    event_type = data.get('type', 'unknown')
                    
                    if event_type == 'sources':
                        sources = data.get('sources', [])
                        print(f"\n📚 [事件 {event_count}] 来源信息:")
                        print(f"   来源数量: {len(sources)}")
                        for i, source in enumerate(sources[:2]):  # 只显示前2个
                            print(f"   来源 {i+1}: {source.get('content', '')[:50]}...")
                    
                    elif event_type == 'token':
                        token_count += 1
                        content = data.get('content', '')
                        full_answer += content
                        print(f"💬 [Token {token_count}] {repr(content)}")
                    
                    elif event_type == 'done':
                        answer = data.get('answer', '')
                        print(f"\n✅ [事件 {event_count}] 完成:")
                        print(f"   完整答案长度: {len(answer)} 字符")
                        print(f"   答案预览: {answer[:100]}...")
                    
                    elif event_type == 'qa_record_id':
                        qa_id = data.get('qa_record_id')
                        print(f"\n💾 [事件 {event_count}] QA 记录 ID: {qa_id}")
                    
                    elif event_type == 'error':
                        error = data.get('error', '')
                        print(f"\n❌ [事件 {event_count}] 错误: {error}")
                    
                    else:
                        print(f"\n❓ [事件 {event_count}] 未知类型: {event_type}")
                        print(f"   数据: {data}")
                
                except json.JSONDecodeError as e:
                    print(f"\n⚠️  JSON 解析失败: {e}")
                    print(f"   原始数据: {data_str}")
    
    print("-"*60)
    print(f"\n📊 统计:")
    print(f"   总事件数: {event_count}")
    print(f"   Token 数: {token_count}")
    print(f"   累积答案长度: {len(full_answer)} 字符")
    
    if full_answer:
        print(f"\n📝 累积的完整答案:")
        print(f"   {full_answer}")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60)

if __name__ == "__main__":
    token = login()
    if token:
        test_streaming(token)

