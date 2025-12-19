"""自动化测试平台服务"""
import requests
import json
from typing import Dict, Any, Optional, List
from app.core.config import settings


class AutomationPlatformService:
    """自动化测试平台服务类"""
    
    def __init__(self, base_url: str, db=None):
        """
        初始化自动化平台服务
        
        Args:
            base_url: 自动化平台API基础地址
            db: 数据库会话，用于AI服务读取配置
        """
        self.base_url = base_url
        if not self.base_url:
            raise ValueError("AUTOMATION_PLATFORM_API_BASE 未配置")
        
        # 移除末尾的斜杠
        self.base_url = self.base_url.rstrip('/')
        
        # 保存数据库连接，用于AI服务
        self.db = db
    
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
                result = response.json()
                
                # 返回 data 部分，这才是真正的用例详情
                if result.get('success') and result.get('data'):
                    case_data = result.get('data')
                    
                    # 打印关键信息以便调试
                    if case_data.get('caseDefine'):
                        case_define = case_data['caseDefine']
                        header_count = len(case_define.get('header', []))
                        body_count = len(case_define.get('body', []))
                        print(f"[INFO] 用例详情包含 caseDefine: header={header_count}个字段, body={body_count}条数据")
                    else:
                        print(f"[WARNING] 用例详情中没有 caseDefine")
                    
                    return case_data
                else:
                    raise Exception(f"获取用例详情失败: {result.get('message', '未知错误')}")
                    
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
            
            # 传入db以读取数据库配置
            ai_service = get_ai_service(self.db)
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
            "type": template_case_detail.get("type", ""),
            "project": template_case_detail.get("project", "")
        }
        
        # 添加circulation信息
        if circulation:
            payload["circulation"] = circulation
        elif template_case_detail.get("circulation"):
            payload["circulation"] = template_case_detail.get("circulation")

        # ??caseDefine??????????header?body?
        if template_case_detail.get("caseDefine") or template_case_detail.get("case_define"):
            case_define_raw = template_case_detail.get("caseDefine") or template_case_detail.get("case_define")

            if isinstance(case_define_raw, str):
                try:
                    case_define = json.loads(case_define_raw)
                except Exception:
                    print(f"[WARNING] caseDefine ????????????????????200??: {case_define_raw[:200]}")
                    case_define = {}
            elif isinstance(case_define_raw, dict):
                case_define = case_define_raw
            else:
                case_define = {}

            header_value = case_define.get("header")
            if isinstance(header_value, str):
                try:
                    header_value = json.loads(header_value)
                except Exception:
                    header_value = []
            case_define["header"] = header_value or []

            body_value = case_define.get("body")
            if isinstance(body_value, str):
                try:
                    body_value = json.loads(body_value)
                except Exception:
                    body_value = None
            if not body_value:
                alt_body = template_case_detail.get("caseBodyList") or template_case_detail.get("case_body_list")
                if isinstance(alt_body, str):
                    try:
                        alt_body = json.loads(alt_body)
                    except Exception:
                        alt_body = None
                body_value = alt_body or []
            case_define["body"] = body_value

            payload["caseDefine"] = case_define
            if body_value:
                payload["caseBodyList"] = body_value

            header_count = len(case_define.get("header", [])) if case_define.get("header") else 0
            body_count = len(case_define.get("body", [])) if case_define.get("body") else 0
            print(f"[INFO] ? caseDefine ???: {header_count} ???(header), {body_count} ?????(body)")
            if body_count == 0:
                print("[WARNING] caseDefine.body ?????????????????????AI?????")
        else:
            print(f"[WARNING] ?? template_case_detail ???caseDefine??")
            print(f"[DEBUG] template_case_detail keys: {list(template_case_detail.keys()) if template_case_detail else 'None'}")
        
        try:
            print(f"[INFO] 调用自动化平台创建用例和明细")
            print(f"[INFO] URL: {url}")
            print(f"[INFO] 用例名称: {name}")
            print(f"[INFO] Payload keys: {list(payload.keys())}")
            try:
                payload_preview = json.dumps(payload, ensure_ascii=False)
                print(f"[DEBUG] 请求体预览（截取1000字符）: {payload_preview[:1000]}")
            except Exception as log_err:
                print(f"[WARNING] 请求体序列化失败: {log_err}")
            
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
    
    def generate_case_body_by_ai(
        self,
        header_fields: List[Dict[str, Any]],
        test_case_info: Dict[str, Any],
        circulation: List[Dict[str, Any]] = None,
        example_body: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        使用AI根据字段定义和测试用例信息生成测试数据(body)
        
        Args:
            header_fields: 字段定义列表（header）
            test_case_info: 测试用例信息
            circulation: 环节信息
            
        Returns:
            生成的测试数据列表（body格式）
        """
        try:
            from app.services.ai_service import get_ai_service
            
            # 传入db以读取数据库配置
            ai_service = get_ai_service(self.db)
            if not ai_service:
                print("[WARNING] AI服务不可用，返回空body")
                return []
            
            # 准备字段信息描述
            fields_desc = []
            for field in header_fields:
                row_name = field.get('rowName', field.get('row', ''))
                row = field.get('row', '')
                field_type = field.get('type', '')
                flag = field.get('flag', '')
                
                field_info = f"- {row_name} (字段名: {row}"
                if field_type:
                    field_info += f", 类型: {field_type}"
                if flag:
                    field_info += f", 标识: {flag}"
                field_info += ")"
                fields_desc.append(field_info)
            
            fields_text = "\n".join(fields_desc)

            example_block = ""
            if example_body:
                try:
                    import json as _json
                    example_block = "\n【示例body（供参考）】\n" + _json.dumps(example_body, ensure_ascii=False, indent=2)
                except Exception:
                    example_block = ""
            
            # 准备环节信息
            circulation_text = ""
            if circulation:
                circ_items = [f"- {c.get('name', '')} ({c.get('vargroup', '')})" for c in circulation]
                circulation_text = "\n循环字段信息：\n" + "\n".join(circ_items)
            
            # 构建AI提示词
            prompt = f"""你是一个自动化测试专家。请根据以下测试用例信息和字段定义，生成1-3条合理的测试数据。

【测试用例信息】
标题：{test_case_info.get('title', '')}
描述：{test_case_info.get('description', '')}
前置条件：{test_case_info.get('preconditions', '')}
测试步骤：{test_case_info.get('test_steps', '')}
预期结果：{test_case_info.get('expected_result', '')}
测试类型：{test_case_info.get('test_type', '')}
优先级：{test_case_info.get('priority', '')}
{circulation_text}

【字段定义】
{fields_text}{example_block}

【要求】
1. 根据测试用例的具体内容，生成符合字段要求的测试数据
2. 测试数据要真实、合理、符合业务逻辑
3. 生成1-3条测试数据，每条数据包含一个用例描述(casedesc)和所有字段的值(var)
4. 字段值要符合字段类型和业务含义
5. 如果字段以 _1, _2 结尾，表示可能有多个同类字段，注意区分
6. 日期格式使用 YYYYMMDD (如：20250120)
7. 代码类字段要使用正确的业务代码

请以JSON格式返回，格式如下：
[
    {{
        "casedesc": "测试数据描述",
        "var": {{
            "字段名1": "值1",
            "字段名2": "值2",
            ...
        }}
    }}
]

只返回JSON数组，不要其他说明文字。"""
            
            print(f"[INFO] 调用AI生成测试数据（基于{len(header_fields)}个字段）")
            print(f"[DEBUG] ========== AI Prompt 开始 ==========")
            print(prompt)
            print(f"[DEBUG] ========== AI Prompt 结束 ==========")
            
            # 调用AI：这里直接调用 llm.invoke，避免 agent/tool_calls 返回 messages 结构导致无法解析JSON
            response = ai_service.llm.invoke(prompt)
            response_str = getattr(response, "content", None)
            if response_str is None:
                response_str = str(response)
            
            print(f"[DEBUG] ========== AI Response 开始 ==========")
            print(response_str)
            print(f"[DEBUG] (AI Response 总长度: {len(response_str)} 字符)")
            print(f"[DEBUG] ========== AI Response 结束 ==========")
            
            # 解析AI返回的JSON
            import re
            
            candidates = []

            # 优先取 detail='[...]'（常见Agent响应包含结构化JSON）
            detail_match = re.search(r"detail='([\s\S]*?)'(?:\s|$)", response_str)
            if detail_match:
                candidate = detail_match.group(1).replace('\\n', '\n').replace("\\'", "'")
                candidates.append(candidate)
                print(f"[DEBUG] 从detail字段提取JSON: {len(candidate)} 字符")

            # 其次尝试 answer='...'（有时 answer 不是JSON，若detail可用则已覆盖）
            answer_match = re.search(r"answer='([\s\S]*?)'(?:\s|$)", response_str)
            if answer_match:
                candidate = answer_match.group(1).replace('\\n', '\n').replace("\\'", "'")
                candidates.append(candidate)
                print(f"[DEBUG] 从answer字段提取JSON: {len(candidate)} 字符")

            # 再尝试 markdown 代码块
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_str)
            if json_match:
                candidates.append(json_match.group(1))

            # 兜底直接整体解析
            candidates.append(response_str.strip())
            
            last_error = None
            body_data = None

            def _parse_candidate(raw: str):
                raw = raw.strip()
                if not raw:
                    raise json.JSONDecodeError("空字符串", raw, 0)
                parse_targets = [raw]

                if "\\n" in raw or "\\r\\n" in raw:
                    normalized = raw.replace("\\r\\n", "\n").replace("\\n", "\n")
                    if normalized not in parse_targets:
                        parse_targets.append(normalized)

                last_inner_error = None
                for target in parse_targets:
                    try:
                        return json.loads(target)
                    except json.JSONDecodeError as err:
                        last_inner_error = err
                        continue

                for target in parse_targets:
                    start_idx = target.find('[')
                    end_idx = target.rfind(']') + 1
                    if start_idx != -1 and end_idx > start_idx:
                        try:
                            return json.loads(target[start_idx:end_idx])
                        except json.JSONDecodeError as err:
                            last_inner_error = err
                    start_idx = target.find('{')
                    end_idx = target.rfind('}') + 1
                    if start_idx != -1 and end_idx > start_idx:
                        try:
                            return json.loads(target[start_idx:end_idx])
                        except json.JSONDecodeError as err:
                            last_inner_error = err

                raise last_inner_error or json.JSONDecodeError("无法解析JSON字符串", raw, 0)

            for candidate in candidates:
                try:
                    body_data = _parse_candidate(candidate)
                    break
                except json.JSONDecodeError as parse_error:
                    last_error = parse_error
                    continue

            if body_data is None:
                raise last_error or json.JSONDecodeError("没有可用的JSON字符串", "", 0)
            
            if not isinstance(body_data, list):
                body_data = [body_data]
            
            print(f"[INFO] ✅ AI生成了 {len(body_data)} 条测试数据")

            result_body = []
            for idx, item in enumerate(body_data, start=1):
                body_item = {
                    "casezf": "1",
                    "casedesc": item.get("casedesc", f"测试数据{idx}"),
                    "var": item.get("var", {}),
                    "hoperesult": "成功结案",
                    "iscaserun": False,
                    "caseBodySN": idx
                }
                result_body.append(body_item)
            
            return result_body
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] 解析AI返回的JSON失败: {e}")
            try:
                if 'response_str' in locals():
                    print(f"[DEBUG] AI返回内容: {response_str[:500]}")
                elif 'response' in locals():
                    print(f"[DEBUG] AI返回内容: {str(response)[:500]}")
                else:
                    print(f"[DEBUG] response未定义")
            except Exception as ex:
                print(f"[DEBUG] 无法打印AI返回内容: {ex}")
            return []
        except Exception as e:
            print(f"[ERROR] AI生成测试数据失败: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
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
        
        # 调试：打印获取到的case_detail结构
        if case_detail:
            print(f"[DEBUG] case_detail keys: {list(case_detail.keys())}")
            if 'caseDefine' in case_detail:
                case_define = case_detail['caseDefine']
                print(f"[DEBUG] caseDefine存在: header={len(case_define.get('header', []))}, body={len(case_define.get('body', []))}")
            else:
                print(f"[WARNING] case_detail中没有caseDefine字段")
        else:
            print(f"[ERROR] case_detail为空")
        
        # 从用例详情中提取字段信息
        fields_data = None
        header_fields = []
        if case_detail:
            if 'caseDefine' in case_detail:
                case_define = case_detail.get('caseDefine', {})
                header_fields = case_define.get('header', [])
                fields_data = header_fields
        
        # 从模板中提取circulation信息
        circulation = selected_case.get('circulation', [])
        
        # 准备tags（可以包含circulation信息）
        tags_data = []
        if circulation:
            for circ in circulation:
                tags_data.append(f"{circ.get('name', '')}({circ.get('vargroup', '')})")
        
        tags = json.dumps(tags_data, ensure_ascii=False) if tags_data else "[]"
        
        # 第四步：使用AI生成测试数据（body）
        print(f"[INFO] 步骤4: 使用AI根据测试用例信息生成测试数据")

        # 提示词示例：从模板body取第一条，帮助AI理解格式
        example_body = None
        if case_detail and case_detail.get('caseDefine'):
            template_body = case_detail['caseDefine'].get('body') or []
            if template_body:
                example_body = template_body[0]

        generated_body = []
        if header_fields and test_case_info:
            generated_body = self.generate_case_body_by_ai(
                header_fields=header_fields,
                test_case_info=test_case_info,
                circulation=circulation,
                example_body=example_body  # 传入示例，提升生成质量
            )

            if generated_body:
                if 'caseDefine' not in case_detail:
                    case_detail['caseDefine'] = {}
                case_detail['caseDefine']['body'] = generated_body
                print(f"[INFO] ✅ 已将AI生成的 {len(generated_body)} 条测试数据添加到caseDefine")
            else:
                raise Exception(
                    "AI未生成测试数据，无法继续创建自动化用例。"
                    "请检查：AI服务、header字段、测试用例信息是否完整。"
                )
        else:
            if not header_fields:
                print(f"[ERROR] 缺少header字段定义，无法生成测试数据")
            if not test_case_info:
                print(f"[ERROR] 缺少测试用例信息，无法生成测试数据")
            raise Exception(
                "缺少生成测试数据的必要信息，无法创建自动化用例。"
            )
        
        # 第五步：一次性创建用例和明细
        print(f"[INFO] 步骤5: 一次性创建用例和明细")
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


# 全局实例（用于不需要数据库配置的场景）
def get_automation_service(db=None) -> Optional[AutomationPlatformService]:
    """
    获取自动化平台服务实例
    
    Args:
        db: 数据库会话，传入后AI服务可读取数据库配置，同时可从数据库读取API地址
        
    Returns:
        AutomationPlatformService 实例
    """
    try:
        # 优先从数据库读取配置
        api_base = None
        if db:
            try:
                from app.models.system_config import SystemConfig
                config = db.query(SystemConfig).filter(
                    SystemConfig.config_key == "AUTOMATION_PLATFORM_API_BASE"
                ).first()
                if config and config.config_value:
                    api_base = config.config_value
                    print(f"[INFO] 从数据库读取自动化平台API地址: {api_base}")
            except Exception as e:
                print(f"[WARNING] 从数据库读取自动化平台配置失败: {e}")
        
        # 回退到环境变量
        if not api_base:
            api_base = settings.AUTOMATION_PLATFORM_API_BASE
            if api_base:
                print(f"[INFO] 从环境变量读取自动化平台API地址: {api_base}")
        
        if not api_base:
            print("[WARNING] 自动化平台 API 地址未配置（数据库和环境变量都未找到）")
            return None
            
        return AutomationPlatformService(base_url=api_base, db=db)
    except Exception as e:
        print(f"[WARNING] 初始化自动化平台服务失败: {e}")
        return None


automation_service = get_automation_service()  # 全局实例（无db）
