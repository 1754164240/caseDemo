"""
测试审批功能
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
        return response.json()["access_token"]
    else:
        print(f"❌ 登录失败: {response.status_code}")
        print(response.text)
        return None

def test_test_point_approval(token):
    """测试测试点审批功能"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "="*60)
    print("测试测试点审批功能")
    print("="*60)
    
    # 1. 获取测试点列表
    print("\n1. 获取测试点列表...")
    response = requests.get(f"{BASE_URL}/test-points/", headers=headers)
    if response.status_code != 200:
        print(f"❌ 获取测试点列表失败: {response.status_code}")
        return
    
    test_points = response.json()
    if not test_points:
        print("❌ 没有测试点数据")
        return
    
    test_point = test_points[0]
    test_point_id = test_point["id"]
    print(f"✅ 找到测试点: ID={test_point_id}, 标题={test_point.get('title', 'N/A')}")
    print(f"   当前审批状态: {test_point.get('approval_status', 'pending')}")
    
    # 2. 审批通过
    print(f"\n2. 审批通过测试点 {test_point_id}...")
    approval_data = {
        "approval_status": "approved",
        "approval_comment": "测试通过，质量良好"
    }
    response = requests.post(
        f"{BASE_URL}/test-points/{test_point_id}/approve",
        headers=headers,
        json=approval_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 审批成功")
        print(f"   审批状态: {result.get('approval_status')}")
        print(f"   审批意见: {result.get('approval_comment')}")
        print(f"   审批时间: {result.get('approved_at')}")
    else:
        print(f"❌ 审批失败: {response.status_code}")
        print(response.text)
        return
    
    # 3. 重置审批状态
    print(f"\n3. 重置测试点 {test_point_id} 的审批状态...")
    response = requests.post(
        f"{BASE_URL}/test-points/{test_point_id}/reset-approval",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 重置成功")
        print(f"   审批状态: {result.get('approval_status')}")
    else:
        print(f"❌ 重置失败: {response.status_code}")
        print(response.text)
        return
    
    # 4. 审批拒绝
    print(f"\n4. 审批拒绝测试点 {test_point_id}...")
    approval_data = {
        "approval_status": "rejected",
        "approval_comment": "测试点描述不够清晰，需要补充更多细节"
    }
    response = requests.post(
        f"{BASE_URL}/test-points/{test_point_id}/approve",
        headers=headers,
        json=approval_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 审批成功")
        print(f"   审批状态: {result.get('approval_status')}")
        print(f"   审批意见: {result.get('approval_comment')}")
    else:
        print(f"❌ 审批失败: {response.status_code}")
        print(response.text)

def test_test_case_approval(token):
    """测试测试用例审批功能"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "="*60)
    print("测试测试用例审批功能")
    print("="*60)
    
    # 1. 获取测试用例列表
    print("\n1. 获取测试用例列表...")
    response = requests.get(f"{BASE_URL}/test-cases/", headers=headers)
    if response.status_code != 200:
        print(f"❌ 获取测试用例列表失败: {response.status_code}")
        return
    
    test_cases = response.json()
    if not test_cases:
        print("❌ 没有测试用例数据")
        return
    
    test_case = test_cases[0]
    test_case_id = test_case["id"]
    print(f"✅ 找到测试用例: ID={test_case_id}, 标题={test_case.get('title', 'N/A')}")
    print(f"   当前审批状态: {test_case.get('approval_status', 'pending')}")
    
    # 2. 审批通过
    print(f"\n2. 审批通过测试用例 {test_case_id}...")
    approval_data = {
        "approval_status": "approved",
        "approval_comment": "测试用例设计合理，覆盖全面"
    }
    response = requests.post(
        f"{BASE_URL}/test-cases/{test_case_id}/approve",
        headers=headers,
        json=approval_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 审批成功")
        print(f"   审批状态: {result.get('approval_status')}")
        print(f"   审批意见: {result.get('approval_comment')}")
        print(f"   审批时间: {result.get('approved_at')}")
    else:
        print(f"❌ 审批失败: {response.status_code}")
        print(response.text)
        return
    
    # 3. 重置审批状态
    print(f"\n3. 重置测试用例 {test_case_id} 的审批状态...")
    response = requests.post(
        f"{BASE_URL}/test-cases/{test_case_id}/reset-approval",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 重置成功")
        print(f"   审批状态: {result.get('approval_status')}")
    else:
        print(f"❌ 重置失败: {response.status_code}")
        print(response.text)
        return
    
    # 4. 审批拒绝
    print(f"\n4. 审批拒绝测试用例 {test_case_id}...")
    approval_data = {
        "approval_status": "rejected",
        "approval_comment": "测试步骤不够详细，预期结果描述不清晰"
    }
    response = requests.post(
        f"{BASE_URL}/test-cases/{test_case_id}/approve",
        headers=headers,
        json=approval_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 审批成功")
        print(f"   审批状态: {result.get('approval_status')}")
        print(f"   审批意见: {result.get('approval_comment')}")
    else:
        print(f"❌ 审批失败: {response.status_code}")
        print(response.text)

def main():
    print("开始测试审批功能...")
    
    # 登录
    token = login()
    if not token:
        return
    
    print(f"✅ 登录成功，获取到 token")
    
    # 测试测试点审批
    test_test_point_approval(token)
    
    # 测试测试用例审批
    test_test_case_approval(token)
    
    print("\n" + "="*60)
    print("✅ 所有测试完成！")
    print("="*60)

if __name__ == "__main__":
    main()

