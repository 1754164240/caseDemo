"""自动化测试平台服务"""
import requests
from typing import Dict, Any, Optional
from app.core.config import settings


class AutomationPlatformService:
    """自动化测试平台服务类"""
    
    def __init__(self):
        self.base_url = settings.AUTOMATION_PLATFORM_API_BASE
        if not self.base_url:
            raise ValueError("AUTOMATION_PLATFORM_API_BASE 未配置")
        
        # 移除末尾的斜杠
        self.base_url = self.base_url.rstrip('/')
    
    def create_case(
        self,
        name: str,
        module_id: str,
        scene_id: str,
        scenario_type: str = "API",
        description: str = "",
        tags: str = "[]",
        node_path: str = "",
        case_type: str = "",
        project: str = "",
        scene_id_module: str = ""
    ) -> Dict[str, Any]:
        """
        创建自动化测试用例
        
        Args:
            name: 测试用例名称
            module_id: 模块ID
            scene_id: 场景ID
            scenario_type: 场景类型，默认 "API"
            description: 描述
            tags: 标签，JSON字符串格式
            node_path: 节点路径
            case_type: 用例类型
            project: 项目
            scene_id_module: 场景ID模块
            
        Returns:
            创建成功的用例信息
        """
        url = f"{self.base_url}/usercase/case/addCase"
        
        payload = {
            "name": name,
            "moduleId": module_id,
            "nodePath": node_path,
            "tags": tags,
            "description": description,
            "type": case_type,
            "project": project,
            "scenarioType": scenario_type,
            "sceneId": scene_id,
            "sceneIdModule": scene_id_module
        }
        
        try:
            print(f"[INFO] 调用自动化平台创建用例")
            print(f"[INFO] URL: {url}")
            print(f"[INFO] Payload: {payload}")
            
            response = requests.post(url, json=payload, timeout=30)
            
            print(f"[INFO] 响应状态码: {response.status_code}")
            print(f"[INFO] 响应头: {dict(response.headers)}")
            print(f"[INFO] 响应内容（前500字符）: {response.text[:500]}")
            
            # 检查HTTP状态码
            response.raise_for_status()
            
            # 尝试解析JSON
            try:
                result = response.json()
            except ValueError as json_error:
                raise Exception(
                    f"API返回的不是有效的JSON格式。"
                    f"状态码: {response.status_code}, "
                    f"Content-Type: {response.headers.get('Content-Type')}, "
                    f"响应内容: {response.text[:200]}"
                )
            
            if result.get('success'):
                return result.get('data', {})
            else:
                raise Exception(result.get('message', '创建用例失败'))
                
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"无法连接到自动化平台: {url}。请检查API地址是否正确，网络是否可达")
        except requests.exceptions.Timeout as e:
            raise Exception(f"调用自动化平台超时（30秒）: {url}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP错误 {response.status_code}: {response.text[:200]}")
        except requests.RequestException as e:
            raise Exception(f"调用自动化平台失败: {str(e)}")
    
    def get_supported_fields(self, scene_id: str, usercase_id: str) -> Dict[str, Any]:
        """
        获取支持的字段
        
        Args:
            scene_id: 场景ID
            usercase_id: 用例ID
            
        Returns:
            支持的字段信息
        """
        url = f"{self.base_url}/api/automation/bom/variable/{scene_id}/{usercase_id}"
        
        try:
            print(f"[INFO] 获取支持的字段")
            print(f"[INFO] URL: {url}")
            
            response = requests.get(url, timeout=30)
            
            print(f"[INFO] 响应状态码: {response.status_code}")
            print(f"[INFO] 响应内容（前500字符）: {response.text[:500]}")
            
            response.raise_for_status()
            
            # 尝试解析JSON
            try:
                return response.json()
            except ValueError as json_error:
                raise Exception(
                    f"API返回的不是有效的JSON格式。"
                    f"状态码: {response.status_code}, "
                    f"响应内容: {response.text[:200]}"
                )
            
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"无法连接到自动化平台: {url}")
        except requests.exceptions.Timeout as e:
            raise Exception(f"调用自动化平台超时（30秒）: {url}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP错误 {response.status_code}: {response.text[:200]}")
        except requests.RequestException as e:
            raise Exception(f"获取字段信息失败: {str(e)}")
    
    def create_case_with_fields(
        self,
        name: str,
        module_id: str,
        scene_id: str,
        scenario_type: str = "API",
        description: str = "",
    ) -> Dict[str, Any]:
        """
        创建用例并获取支持的字段
        
        Args:
            name: 测试用例名称
            module_id: 模块ID
            scene_id: 场景ID
            scenario_type: 场景类型
            description: 描述
            
        Returns:
            包含用例信息和支持字段的字典
        """
        # 第一步：创建用例
        case_data = self.create_case(
            name=name,
            module_id=module_id,
            scene_id=scene_id,
            scenario_type=scenario_type,
            description=description
        )
        
        usercase_id = case_data.get('usercaseId')
        if not usercase_id:
            raise Exception("创建用例成功但未返回 usercaseId")
        
        # 第二步：获取支持的字段
        try:
            fields_data = self.get_supported_fields(scene_id, usercase_id)
        except Exception as e:
            print(f"[WARNING] 获取字段信息失败: {e}")
            fields_data = None
        
        return {
            "case": case_data,
            "fields": fields_data,
            "usercase_id": usercase_id,
            "scene_id": scene_id
        }


# 全局实例
def get_automation_service() -> Optional[AutomationPlatformService]:
    """获取自动化平台服务实例"""
    try:
        if not settings.AUTOMATION_PLATFORM_API_BASE:
            print("[WARNING] 自动化平台 API 地址未配置")
            return None
        return AutomationPlatformService()
    except Exception as e:
        print(f"[WARNING] 初始化自动化平台服务失败: {e}")
        return None


automation_service = get_automation_service()

