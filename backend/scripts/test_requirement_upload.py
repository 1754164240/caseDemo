"""
测试需求文档上传和处理功能
"""
import requests
import time

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

def test_upload_requirement(token):
    """测试上传需求文档"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "="*60)
    print("测试需求文档上传和处理")
    print("="*60)
    
    # 检查是否有测试文件
    import os
    test_file = "./uploads/20251110_092223_JXRS250924R044 新产品规格说明书-契约-BANTBC-V1.0.xlsx"
    
    if not os.path.exists(test_file):
        print(f"❌ 测试文件不存在: {test_file}")
        print("请确保测试文件存在")
        return
    
    print(f"\n1. 上传需求文档: {os.path.basename(test_file)}")
    
    # 上传文件
    with open(test_file, 'rb') as f:
        files = {'file': (os.path.basename(test_file), f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        data = {
            'title': '测试需求 - BANTBC 新产品规格',
            'description': '测试需求文档上传和 AI 处理功能'
        }
        
        response = requests.post(
            f"{BASE_URL}/requirements/",
            headers=headers,
            files=files,
            data=data
        )
    
    if response.status_code != 200:
        print(f"❌ 上传失败: {response.status_code}")
        print(response.text)
        return
    
    requirement = response.json()
    requirement_id = requirement['id']
    print(f"✅ 需求文档上传成功")
    print(f"   需求 ID: {requirement_id}")
    print(f"   标题: {requirement['title']}")
    print(f"   状态: {requirement['status']}")
    
    # 等待后台处理
    print(f"\n2. 等待后台处理...")
    max_wait = 60  # 最多等待 60 秒
    wait_time = 0
    
    while wait_time < max_wait:
        time.sleep(2)
        wait_time += 2
        
        # 查询需求状态
        response = requests.get(
            f"{BASE_URL}/requirements/{requirement_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"❌ 查询失败: {response.status_code}")
            break
        
        requirement = response.json()
        status = requirement['status']
        
        print(f"   [{wait_time}s] 状态: {status}")
        
        if status == 'completed':
            print(f"✅ 处理完成！")
            break
        elif status == 'failed':
            print(f"❌ 处理失败")
            break
    
    if wait_time >= max_wait:
        print(f"⚠️ 等待超时")
        return
    
    # 查询生成的测试点
    print(f"\n3. 查询生成的测试点...")
    response = requests.get(
        f"{BASE_URL}/test-points/",
        headers=headers,
        params={'requirement_id': requirement_id}
    )
    
    if response.status_code != 200:
        print(f"❌ 查询测试点失败: {response.status_code}")
        return
    
    test_points = response.json()
    print(f"✅ 成功生成 {len(test_points)} 个测试点")
    
    if test_points:
        print(f"\n测试点列表:")
        for i, tp in enumerate(test_points[:5], 1):  # 只显示前 5 个
            print(f"   {i}. [{tp['code']}] {tp['title']}")
            print(f"      分类: {tp['category']}, 优先级: {tp['priority']}")
            print(f"      审批状态: {tp.get('approval_status', 'pending')}")
    
    if len(test_points) > 5:
        print(f"   ... 还有 {len(test_points) - 5} 个测试点")

def main():
    print("开始测试需求文档上传功能...")
    
    # 登录
    token = login()
    if not token:
        return
    
    print(f"✅ 登录成功")
    
    # 测试上传需求
    test_upload_requirement(token)
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60)

if __name__ == "__main__":
    main()

