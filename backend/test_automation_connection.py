"""测试自动化平台连接的诊断工具"""
import requests
import json
from app.core.config import settings

def test_automation_platform():
    """测试自动化平台的连接和配置"""
    
    print("=" * 60)
    print("自动化测试平台连接诊断工具")
    print("=" * 60)
    
    # 1. 检查配置
    print("\n[步骤 1] 检查配置")
    api_base = settings.AUTOMATION_PLATFORM_API_BASE
    
    if not api_base:
        print("❌ 错误: AUTOMATION_PLATFORM_API_BASE 未配置")
        print("   请在 .env 文件中配置: AUTOMATION_PLATFORM_API_BASE=http://your-platform.com")
        return
    
    print(f"✅ API地址已配置: {api_base}")
    
    # 2. 测试连接
    print("\n[步骤 2] 测试基础连接")
    try:
        response = requests.get(api_base, timeout=5)
        print(f"✅ 可以连接到: {api_base}")
        print(f"   状态码: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到: {api_base}")
        print("   可能原因:")
        print("   1. API地址配置错误")
        print("   2. 服务未启动")
        print("   3. 网络不可达")
        return
    except requests.exceptions.Timeout:
        print(f"⚠️  连接超时: {api_base}")
        return
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return
    
    # 3. 测试创建用例接口
    print("\n[步骤 3] 测试创建用例接口")
    create_case_url = f"{api_base.rstrip('/')}/usercase/case/addCase"
    print(f"接口URL: {create_case_url}")
    
    # 构建测试payload
    test_payload = {
        "name": "测试用例-连接测试",
        "moduleId": "test-module-id",
        "nodePath": "",
        "tags": "[]",
        "description": "这是一个连接测试用例",
        "type": "",
        "project": "",
        "scenarioType": "API",
        "sceneId": "test-scene-id",
        "sceneIdModule": ""
    }
    
    print("\n测试请求体:")
    print(json.dumps(test_payload, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(create_case_url, json=test_payload, timeout=30)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"\n响应内容（前1000字符）:")
        print(response.text[:1000])
        
        # 尝试解析JSON
        try:
            result = response.json()
            print("\n✅ 响应是有效的JSON格式")
            print("\nJSON结构:")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
            
            if result.get('success'):
                print("\n✅ API调用成功")
                if 'data' in result:
                    print("返回数据:")
                    print(json.dumps(result['data'], indent=2, ensure_ascii=False)[:500])
            else:
                print(f"\n⚠️  API返回失败: {result.get('message', '未知错误')}")
                
        except ValueError as e:
            print(f"\n❌ 响应不是有效的JSON格式")
            print(f"   错误: {e}")
            print("\n这通常意味着:")
            print("   1. API地址配置错误（可能返回了HTML错误页面）")
            print("   2. API未正确实现（应该返回JSON格式）")
            print("   3. 服务器内部错误")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到接口: {create_case_url}")
    except requests.exceptions.Timeout:
        print(f"⚠️  接口调用超时")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
    
    # 4. 测试获取字段接口
    print("\n[步骤 4] 测试获取字段接口")
    get_fields_url = f"{api_base.rstrip('/')}/api/automation/bom/variable/test-scene/test-case"
    print(f"接口URL: {get_fields_url}")
    
    try:
        response = requests.get(get_fields_url, timeout=10)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容（前500字符）:")
        print(response.text[:500])
        
        try:
            result = response.json()
            print("\n✅ 响应是有效的JSON格式")
        except ValueError:
            print("\n❌ 响应不是有效的JSON格式")
            
    except Exception as e:
        print(f"⚠️  测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
    
    print("\n建议:")
    print("1. 确保自动化测试平台服务已启动")
    print("2. 确认API地址配置正确（包括协议、域名、端口）")
    print("3. 确认网络可以访问该地址")
    print("4. 检查API是否需要认证（Token/API Key）")
    print("5. 查看上述测试结果，根据错误信息调整配置")


if __name__ == "__main__":
    test_automation_platform()

