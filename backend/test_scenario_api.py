"""
场景管理 API 测试脚本

使用方法:
1. 确保后端服务已启动
2. 替换下面的 TOKEN 变量为有效的 JWT Token
3. 运行脚本: python test_scenario_api.py
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token_here"  # 替换为你的 JWT Token

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def print_response(title, response):
    """打印响应信息"""
    print(f"\n{'=' * 60}")
    print(f"📋 {title}")
    print(f"{'=' * 60}")
    print(f"状态码: {response.status_code}")
    try:
        data = response.json()
        print(f"响应数据:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
    except:
        print(f"响应文本: {response.text}")
    print(f"{'=' * 60}\n")


def test_create_scenarios():
    """测试创建场景"""
    scenarios = [
        {
            "scenario_code": "SC-CONTRACT-001",
            "name": "在线投保",
            "description": "用户通过移动端APP进行在线投保流程",
            "business_line": "contract",
            "channel": "移动端",
            "module": "投保模块",
            "is_active": True
        },
        {
            "scenario_code": "SC-PRESERVATION-001",
            "name": "保单变更",
            "description": "客户通过线上渠道申请保单信息变更",
            "business_line": "preservation",
            "channel": "线上",
            "module": "保全模块",
            "is_active": True
        },
        {
            "scenario_code": "SC-CLAIM-001",
            "name": "理赔申请",
            "description": "客户提交理赔申请并上传相关资料",
            "business_line": "claim",
            "channel": "移动端",
            "module": "理赔模块",
            "is_active": True
        }
    ]
    
    created_ids = []
    for scenario in scenarios:
        response = requests.post(
            f"{BASE_URL}/scenarios/",
            headers=headers,
            json=scenario
        )
        print_response(f"创建场景: {scenario['name']}", response)
        
        if response.status_code == 200:
            created_ids.append(response.json()['id'])
    
    return created_ids


def test_list_scenarios():
    """测试获取场景列表"""
    # 获取所有场景
    response = requests.get(f"{BASE_URL}/scenarios/", headers=headers)
    print_response("获取所有场景", response)
    
    # 按业务线筛选
    response = requests.get(
        f"{BASE_URL}/scenarios/",
        headers=headers,
        params={"business_line": "contract"}
    )
    print_response("筛选契约业务线场景", response)
    
    # 搜索场景
    response = requests.get(
        f"{BASE_URL}/scenarios/",
        headers=headers,
        params={"search": "投保"}
    )
    print_response("搜索包含'投保'的场景", response)


def test_get_scenario(scenario_id):
    """测试获取单个场景"""
    response = requests.get(f"{BASE_URL}/scenarios/{scenario_id}", headers=headers)
    print_response(f"获取场景 ID: {scenario_id}", response)


def test_get_scenario_by_code(scenario_code):
    """测试通过编号获取场景"""
    response = requests.get(
        f"{BASE_URL}/scenarios/code/{scenario_code}",
        headers=headers
    )
    print_response(f"通过编号获取场景: {scenario_code}", response)


def test_update_scenario(scenario_id):
    """测试更新场景"""
    update_data = {
        "description": "更新后的场景描述 - 测试更新功能",
        "channel": "全渠道"
    }
    
    response = requests.put(
        f"{BASE_URL}/scenarios/{scenario_id}",
        headers=headers,
        json=update_data
    )
    print_response(f"更新场景 ID: {scenario_id}", response)


def test_toggle_status(scenario_id):
    """测试切换场景状态"""
    response = requests.post(
        f"{BASE_URL}/scenarios/{scenario_id}/toggle-status",
        headers=headers
    )
    print_response(f"切换场景状态 ID: {scenario_id}", response)


def test_delete_scenario(scenario_id):
    """测试删除场景"""
    response = requests.delete(
        f"{BASE_URL}/scenarios/{scenario_id}",
        headers=headers
    )
    print_response(f"删除场景 ID: {scenario_id}", response)


def run_all_tests():
    """运行所有测试"""
    print("\n🚀 开始测试场景管理 API...\n")
    
    # 1. 创建场景
    print("📝 步骤 1: 创建测试场景")
    created_ids = test_create_scenarios()
    
    if not created_ids:
        print("❌ 创建场景失败，请检查 TOKEN 是否有效")
        return
    
    # 2. 获取场景列表
    print("\n📋 步骤 2: 获取场景列表")
    test_list_scenarios()
    
    # 3. 获取单个场景
    print("\n🔍 步骤 3: 获取单个场景")
    test_get_scenario(created_ids[0])
    
    # 4. 通过编号获取场景
    print("\n🔍 步骤 4: 通过编号获取场景")
    test_get_scenario_by_code("SC-CONTRACT-001")
    
    # 5. 更新场景
    print("\n✏️ 步骤 5: 更新场景")
    test_update_scenario(created_ids[0])
    
    # 6. 切换场景状态
    print("\n🔄 步骤 6: 切换场景状态")
    test_toggle_status(created_ids[0])
    test_toggle_status(created_ids[0])  # 再次切换回来
    
    # 7. 删除场景
    print("\n🗑️ 步骤 7: 删除场景")
    for scenario_id in created_ids:
        test_delete_scenario(scenario_id)
    
    print("\n✅ 所有测试完成！")


if __name__ == "__main__":
    if TOKEN == "your_jwt_token_here":
        print("⚠️ 请先替换脚本中的 TOKEN 变量为有效的 JWT Token")
        print("💡 提示：你可以通过登录接口获取 Token")
        print("\n示例：")
        print("curl -X POST 'http://localhost:8000/api/v1/auth/login' \\")
        print("  -H 'Content-Type: application/json' \\")
        print("  -d '{\"username\": \"your_username\", \"password\": \"your_password\"}'")
    else:
        run_all_tests()

