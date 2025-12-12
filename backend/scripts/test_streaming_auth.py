"""
测试流式 API 的认证
"""
import requests

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
        print(f"Token: {token[:50]}...")
        return token
    else:
        print(f"❌ 登录失败: {response.status_code}")
        print(response.text)
        return None

def test_streaming(token):
    """测试流式 API"""
    print("\n测试流式 API...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "question": "测试问题",
        "collection_name": "knowledge_base",
        "top_k": 5,
        "return_source": True
    }
    
    response = requests.post(
        f"{BASE_URL}/knowledge-base/query/stream",
        headers=headers,
        json=data,
        stream=True
    )
    
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    
    if response.status_code == 200:
        print("✅ 流式 API 认证成功")
        print("\n流式响应:")
        for line in response.iter_lines():
            if line:
                print(line.decode('utf-8'))
    else:
        print(f"❌ 流式 API 失败")
        print(response.text)

if __name__ == "__main__":
    token = login()
    if token:
        test_streaming(token)

