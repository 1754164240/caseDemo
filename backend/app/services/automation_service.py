"""自动化测试平台服务"""
import requests
import json
from typing import Dict, Any, Optional, List
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
    
    def get_scene_cases(self, scene_id: str) -> list:
        """
        根据场景ID获取用例列表
        
        Args:
            scene_id: 场景ID
            
        Returns:
            用例列表
        """
        url = f"{self.base_url}/ai/case/queryBySceneId/{scene_id}"
        
        try:
            print(f"[INFO] 获取场景用例列表")
            print(f"[INFO] URL: {url}")
            
            response = requests.get(url, timeout=30)
            
            print(f"[INFO] 响应状态码: {response.status_code}")
            print(f"[INFO] 响应内容（前500字符）: {response.text[:500]}")
            
            response.raise_for_status()
            
            # 尝试解析JSON
            try:
                result = response.json()
                if result.get('success'):
                    return result.get('data', [])
                else:
                    raise Exception(result.get('message', '获取用例列表失败'))
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
            raise Exception(f"获取用例列表失败: {str(e)}")
    
    def get_case_detail(self, usercase_id: str) -> Dict[str, Any]:
        """
        根据用例ID获取用例详细信息
        
        Args:
            usercase_id: 用例ID
            
        Returns:
            用例详细信息
        """
        url = f"{self.base_url}/ai/case/queryCaseBody/{usercase_id}"
        
        try:
            print(f"[INFO] 获取用例详细信息")
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
            raise Exception(f"获取用例详情失败: {str(e)}")
    
    def select_best_case_by_ai(
        self,
        test_case_info: Dict[str, Any],
        available_cases: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        使用AI选择最匹配的用例
        
        Args:
            test_case_info: 测试用例信息（标题、描述等）
            available_cases: 可用的用例列表
            
        Returns:
            选中的用例（包含完整信息），如果没有合适的返回None
        """
        try:
            from app.services.ai_service import get_ai_service
            
            ai_service = get_ai_service()
            if not ai_service:
                print("[WARNING] AI服务不可用，使用第一个用例")
                return available_cases[0] if available_cases else None
            
            # 构建用例列表，确保安全处理数据
            cases_for_ai = []
            for idx, c in enumerate(available_cases):
                case_info = {
                    'index': idx,
                    'usercaseId': str(c.get('usercaseId', '')),
                    'name': str(c.get('name', '')),
                    'description': str(c.get('description', ''))
                }
                cases_for_ai.append(case_info)
            
            # 准备prompt
            prompt = f"""你是一个自动化测试专家。我需要为以下测试用例选择最匹配的自动化平台用例模板。

测试用例信息：
- 标题：{test_case_info.get('title', '')}
- 描述：{test_case_info.get('description', '')}
- 前置条件：{test_case_info.get('preconditions', '')}
- 测试步骤：{test_case_info.get('test_steps', '')}
- 预期结果：{test_case_info.get('expected_result', '')}

可选的自动化用例模板：
{json.dumps(cases_for_ai, ensure_ascii=False, indent=2)}

请分析测试用例的内容，选择最匹配的自动化用例模板。
只需要返回选中的usercaseId，不要返回其他内容。
如果没有合适的，返回第一个用例的usercaseId。"""

            print(f"[INFO] 使用AI选择最佳用例...")
            print(f"[DEBUG] 可选用例数量: {len(available_cases)}")
            
            response = ai_service.llm.invoke(prompt)
            
            selected_id = response.content.strip()
            print(f"[INFO] AI选择的用例ID: {selected_id}")
            
            # 查找匹配的用例
            for c in available_cases:
                if str(c.get('usercaseId', '')) == selected_id:
                    print(f"[INFO] 找到匹配的用例: {c.get('name', '')}")
                    return c
            
            print(f"[WARNING] AI返回的ID无效，使用第一个用例")
            return available_cases[0] if available_cases else None
                
        except Exception as e:
            print(f"[ERROR] AI选择用例失败: {e}")
            import traceback
            traceback.print_exc()
            return available_cases[0] if available_cases else None
    
    def create_case_and_body(
        self,
        name: str,
        module_id: str,
        scene_id: str,
        template_case_detail: Dict[str, Any],
        scenario_type: str = "API",
        description: str = "",
        tags: str = "[]",
        circulation: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        一次性创建用例和明细（基于模板）
        
        Args:
            name: 测试用例名称
            module_id: 模块ID
            scene_id: 场景ID
            template_case_detail: 模板用例的完整详情对象
            scenario_type: 场景类型
            description: 描述
            tags: 标签
            circulation: 环节信息
            
        Returns:
            创建成功的用例信息
        """
        url = f"{self.base_url}/ai/case/createCaseAndBody"
        
        # 构建请求payload，使用模板的caseDefine结构
        payload = {
            "name": name,
            "moduleId": module_id,
            "sceneId": scene_id,
            "scenarioType": scenario_type,
            "description": description,
            "tags": tags,
            "nodePath": "",
            "type": template_case_detail.get("type", ""),
            "project": template_case_detail.get("project", ""),
            "sceneIdModule": ""
        }
        
        # 添加circulation信息
        if circulation:
            payload["circulation"] = circulation
        elif template_case_detail.get("circulation"):
            payload["circulation"] = template_case_detail.get("circulation")
        
        # 添加caseDefine（用例明细结构，包含header和body）
        if template_case_detail.get("caseDefine"):
            case_define = template_case_detail.get("caseDefine")
            payload["caseDefine"] = case_define
            
            # 日志显示结构信息
            header_count = len(case_define.get("header", [])) if case_define.get("header") else 0
            body_count = len(case_define.get("body", [])) if case_define.get("body") else 0
            print(f"[INFO] caseDefine 包含 {header_count} 个字段(header), {body_count} 个测试数据(body)")
        
        try:
            print(f"[INFO] 调用自动化平台创建用例和明细")
            print(f"[INFO] URL: {url}")
            print(f"[INFO] 用例名称: {name}")
            print(f"[INFO] Payload keys: {list(payload.keys())}")
            
            # 显示circulation和caseDefine信息
            if payload.get("circulation"):
                print(f"[INFO] Circulation: {len(payload['circulation'])} 个环节")
            if payload.get("caseDefine"):
                print(f"[INFO] CaseDefine: header={len(payload['caseDefine'].get('header', []))}, body={len(payload['caseDefine'].get('body', []))}")
            
            response = requests.post(url, json=payload, timeout=30)
            
            print(f"[INFO] 响应状态码: {response.status_code}")
            print(f"[INFO] 响应内容（前500字符）: {response.text[:500]}")
            
            response.raise_for_status()
            
            try:
                result = response.json()
            except ValueError as json_error:
                raise Exception(
                    f"API返回的不是有效的JSON格式。"
                    f"状态码: {response.status_code}, "
                    f"响应内容: {response.text[:200]}"
                )
            
            if result.get('success'):
                print(f"[INFO] 用例和明细创建成功")
                return result.get('data', {})
            else:
                raise Exception(result.get('message', '创建用例和明细失败'))
                
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"无法连接到自动化平台: {url}")
        except requests.exceptions.Timeout as e:
            raise Exception(f"调用自动化平台超时（30秒）: {url}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP错误 {response.status_code}: {response.text[:200]}")
        except requests.RequestException as e:
            raise Exception(f"创建用例和明细失败: {str(e)}")
    
    def create_case_with_fields(
        self,
        name: str,
        module_id: str,
        scene_id: str,
        scenario_type: str = "API",
        description: str = "",
        test_case_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        基于AI匹配的模板一次性创建自动化用例和明细
        
        新流程：
        1. 根据场景ID获取用例列表
        2. 使用AI筛选最匹配的用例
        3. 根据用例ID获取用例详情
        4. 使用模板一次性创建用例和明细
        
        Args:
            name: 测试用例名称
            module_id: 模块ID
            scene_id: 场景ID
            scenario_type: 场景类型
            description: 描述
            test_case_info: 测试用例详细信息（用于AI匹配）
            
        Returns:
            包含创建的用例信息和字段的字典
        """
        # 第一步：获取场景的用例列表
        print(f"[INFO] 步骤1: 获取场景 {scene_id} 的用例列表")
        scene_cases = self.get_scene_cases(scene_id)
        
        if not scene_cases:
            raise Exception(f"场景 {scene_id} 下没有可用的用例")
        
        print(f"[INFO] 找到 {len(scene_cases)} 个可用用例")
        
        # 第二步：使用AI选择最匹配的用例
        print(f"[INFO] 步骤2: 使用AI选择最匹配的用例")
        if test_case_info:
            selected_case = self.select_best_case_by_ai(test_case_info, scene_cases)
        else:
            # 如果没有提供测试用例信息，使用第一个
            selected_case = scene_cases[0]
            print(f"[INFO] 未提供测试用例信息，使用第一个用例")
        
        if not selected_case:
            raise Exception("无法选择合适的用例")
        
        selected_usercase_id = selected_case.get('usercaseId')
        print(f"[INFO] 选中的用例ID: {selected_usercase_id}")
        print(f"[INFO] 选中的用例名称: {selected_case.get('name', '')}")
        
        # 第三步：获取用例详情
        print(f"[INFO] 步骤3: 获取用例详情")
        case_detail = self.get_case_detail(selected_usercase_id)
        
        # 从用例详情中提取字段信息
        fields_data = None
        if case_detail:
            if 'caseDefine' in case_detail:
                case_define = case_detail.get('caseDefine', {})
                fields_data = case_define.get('header', [])
        
        # 从模板中提取circulation信息
        circulation = selected_case.get('circulation', [])
        
        # 准备tags（可以包含circulation信息）
        tags_data = []
        if circulation:
            for circ in circulation:
                tags_data.append(f"{circ.get('name', '')}({circ.get('vargroup', '')})")
        
        tags = json.dumps(tags_data, ensure_ascii=False) if tags_data else "[]"
        
        # 第四步：一次性创建用例和明细
        print(f"[INFO] 步骤4: 一次性创建用例和明细")
        print(f"[INFO] 使用模板的circulation信息: {circulation}")
        
        case_data = self.create_case_and_body(
            name=name,
            module_id=module_id,
            scene_id=scene_id,
            template_case_detail=case_detail,
            scenario_type=scenario_type,
            description=description,
            tags=tags,
            circulation=circulation
        )
        
        new_usercase_id = case_data.get('usercaseId')
        if not new_usercase_id:
            raise Exception("创建用例成功但未返回 usercaseId")
        
        print(f"[INFO] 创建的新用例ID: {new_usercase_id}")
        
        # 返回完整信息
        return {
            "created_case": case_data,           # 创建的新用例信息
            "template_case": selected_case,      # 使用的模板用例
            "case_detail": case_detail,          # 模板用例详情
            "fields": fields_data,               # 字段信息
            "new_usercase_id": new_usercase_id,  # 新创建的用例ID
            "template_usercase_id": selected_usercase_id,  # 模板用例ID
            "scene_id": scene_id,
            "selected_template": {
                "usercaseId": selected_usercase_id,
                "name": selected_case.get('name', ''),
                "description": selected_case.get('description', ''),
                "circulation": circulation
            }
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

