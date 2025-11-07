"""
测试新的测试步骤格式
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

print("当前测试用例数据:")
print(f"标题: {test_case['title']}")
print(f"编号: {test_case['code']}")
print("\n测试步骤:")
for step in test_case['test_steps']:
    print(f"  步骤 {step['step']}:")
    print(f"    操作: {step['action']}")
    print(f"    预期: {step['expected']}")

# 使用新格式更新测试用例
update_data = {
    "title": "测试新格式 - 疑似同一客户标志组合测试",
    "description": "验证新的测试步骤录入格式",
    "test_steps": [
        {
            "step": 1,
            "action": "创建理赔案件，设置理赔类型为身故，险种为BANTBC",
            "expected": "案件创建成功，进入录入环节"
        },
        {
            "step": 2,
            "action": "为案件设置疑似同一客户标志",
            "expected": "标志设置成功"
        },
        {
            "step": 3,
            "action": "同时设置身份证件有效期超期问题",
            "expected": "多重检核问题设置成功"
        },
        {
            "step": 4,
            "action": "完成案件录入并提交至自核环节",
            "expected": "案件成功进入自核环节"
        },
        {
            "step": 5,
            "action": "执行自核操作",
            "expected": "自核被阻止，系统显示多条检核规则提示信息"
        }
    ]
}

print("\n" + "=" * 60)
print("发送更新请求...")

update_response = requests.put(
    "http://localhost:8000/api/v1/test-cases/6",
    headers={"Authorization": f"Bearer {token}"},
    json=update_data
)

print(f"状态码: {update_response.status_code}")

if update_response.status_code == 200:
    print("✅ 更新成功!")
    result = update_response.json()
    print(f"\n更新后的标题: {result['title']}")
    print("\n更新后的测试步骤:")
    for step in result['test_steps']:
        print(f"  步骤 {step['step']}:")
        print(f"    操作: {step['action']}")
        print(f"    预期: {step['expected']}")
else:
    print("❌ 更新失败:")
    print(update_response.text)

