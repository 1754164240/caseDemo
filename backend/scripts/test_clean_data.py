"""
清理测试用例 6 的数据，移除重复的序号和预期
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
test_case = get_response.json()

print("原始数据:")
print(json.dumps(test_case['test_steps'], indent=2, ensure_ascii=False))

# 清理 test_steps 数据
import re

cleaned_steps = []
for item in test_case['test_steps']:
    action = item['action']
    expected = item.get('expected', '')

    # 去掉开头的序号
    action = re.sub(r'^\d+\.\s*', '', action)
    # 去掉末尾的 " - 预期:" 部分
    if ' - 预期:' in action:
        parts = action.split(' - 预期:')
        action = parts[0].strip()
        if len(parts) > 1 and parts[1].strip() and not expected:
            expected = parts[1].strip()

    cleaned_steps.append({
        "step": item['step'],
        "action": action,
        "expected": expected
    })

print("\n清理后的数据:")
print(json.dumps(cleaned_steps, indent=2, ensure_ascii=False))

# 更新测试用例
update_data = {
    "test_steps": cleaned_steps
}

update_response = requests.put(
    "http://localhost:8000/api/v1/test-cases/6",
    headers={"Authorization": f"Bearer {token}"},
    json=update_data
)

print("\n更新响应:")
print(f"状态码: {update_response.status_code}")
if update_response.status_code == 200:
    print("✅ 数据清理成功!")
    print(json.dumps(update_response.json()['test_steps'], indent=2, ensure_ascii=False))
else:
    print("❌ 更新失败:")
    print(update_response.text)

