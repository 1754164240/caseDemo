"""
清理所有测试用例的数据，移除重复的序号和预期
"""
import requests
import json
import re

# 登录获取 token
login_response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    data={"username": "admin", "password": "admin123"}
)
token = login_response.json()["access_token"]

# 获取所有测试用例
get_response = requests.get(
    "http://localhost:8000/api/v1/test-cases/",
    headers={"Authorization": f"Bearer {token}"}
)
test_cases = get_response.json()

print(f"找到 {len(test_cases)} 个测试用例")
print("=" * 60)

updated_count = 0
for test_case in test_cases:
    test_case_id = test_case['id']
    test_case_code = test_case.get('code', f'ID-{test_case_id}')
    test_steps = test_case.get('test_steps', [])
    
    if not test_steps or not isinstance(test_steps, list):
        print(f"跳过 {test_case_code}: 没有测试步骤或格式不正确")
        continue
    
    # 检查是否需要清理
    needs_cleaning = False
    for item in test_steps:
        if isinstance(item, dict):
            action = item.get('action', '')
            # 检查是否有序号或重复的预期
            if re.match(r'^\d+\.\s', action) or action.endswith(' - 预期:'):
                needs_cleaning = True
                break
    
    if not needs_cleaning:
        print(f"跳过 {test_case_code}: 数据已经是干净的")
        continue
    
    # 清理 test_steps 数据
    cleaned_steps = []
    for item in test_steps:
        if not isinstance(item, dict):
            cleaned_steps.append(item)
            continue
            
        action = item.get('action', '')
        expected = item.get('expected', '')
        step = item.get('step', len(cleaned_steps) + 1)
        
        # 去掉开头的序号
        action = re.sub(r'^\d+\.\s*', '', action)
        
        # 去掉末尾的 " - 预期:" 部分
        if ' - 预期:' in action:
            parts = action.split(' - 预期:')
            action = parts[0].strip()
            # 如果分割后有内容且 expected 为空，则使用分割出的内容
            if len(parts) > 1 and parts[1].strip() and not expected:
                expected = parts[1].strip()
        
        cleaned_steps.append({
            "step": step,
            "action": action,
            "expected": expected
        })
    
    # 更新测试用例
    update_data = {
        "test_steps": cleaned_steps
    }
    
    try:
        update_response = requests.put(
            f"http://localhost:8000/api/v1/test-cases/{test_case_id}",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data
        )
        
        if update_response.status_code == 200:
            print(f"✅ {test_case_code}: 清理成功")
            updated_count += 1
        else:
            print(f"❌ {test_case_code}: 更新失败 (状态码: {update_response.status_code})")
            print(f"   错误: {update_response.text}")
    except Exception as e:
        print(f"❌ {test_case_code}: 更新异常 - {str(e)}")

print("=" * 60)
print(f"清理完成! 共更新了 {updated_count} 个测试用例")

