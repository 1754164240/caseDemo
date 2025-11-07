import requests

login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data={"username": "admin", "password": "admin123"}
)
token = login_response.json()["access_token"]

update_response = requests.put(
    "http://localhost:8000/api/v1/test-cases/6",
    headers={"Authorization": f"Bearer {token}"},
    json={"title": "疑似同一客户标志与其他检核规则组合测试"}
)

print(f"状态码: {update_response.status_code}")
if update_response.status_code == 200:
    print("✅ 标题已恢复")
else:
    print(f"❌ 恢复失败: {update_response.text}")

