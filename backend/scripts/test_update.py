"""
测试更新测试用例的请求
"""
import requests
import json

# 登录获取 token
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data={"username": "admin", "password": "admin123"}
)
token = login_response.json()["access_token"]

# 获取测试用例 6 的详情
get_response = requests.get(
    "http://localhost:8000/api/v1/test-cases/6",
    headers={"Authorization": f"Bearer {token}"}
)
print("获取测试用例详情:")
print(json.dumps(get_response.json(), indent=2, ensure_ascii=False))

# 尝试更新测试用例
update_data = {
    "title": "测试更新标题",
    "description": "测试更新描述",
    "preconditions": "测试前置条件",
    "test_steps": [
        {"step": 1, "action": "步骤1", "expected": "期望1"},
        {"step": 2, "action": "步骤2", "expected": "期望2"}
    ],
    "expected_result": "测试预期结果",
    "priority": "high",
    "test_type": "functional"
}

print("\n发送更新请求:")
print(json.dumps(update_data, indent=2, ensure_ascii=False))

update_response = requests.put(
    "http://localhost:8000/api/v1/test-cases/6",
    headers={"Authorization": f"Bearer {token}"},
    json=update_data
)

print("\n更新响应:")
print(f"状态码: {update_response.status_code}")
print(json.dumps(update_response.json(), indent=2, ensure_ascii=False))

