"""基于 LangGraph 的自动化用例生成工作流服务 - 使用 interrupt 实现人工审核"""

from typing import Dict, Any, Optional, List, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from typing_extensions import TypedDict
import json
import os
import sqlite3

from .automation_service import get_automation_service
from .field_metadata_service import FieldMetadataService
from .body_validator import BodyValidator


# 定义状态类型
class AutomationCaseState(TypedDict, total=False):
    """自动化用例生成状态"""

    # 输入参数
    test_case_id: int
    name: Optional[str]
    module_id: Optional[str]
    scene_id: Optional[str]
    scenario_type: str
    description: str
    test_case_info: Optional[Dict]

    # AI匹配场景相关
    available_scenarios: List[Dict]
    matched_scenario: Optional[Dict]

    # 流程中间状态
    scene_cases: List[Dict]
    selected_case: Optional[Dict]
    selected_usercase_id: Optional[str]
    case_detail: Optional[Dict]
    header_fields: List[Dict]
    circulation: List[Dict]

    # 元数据和规则
    field_metadata: Optional[Dict]
    linkage_rules: List[Dict]

    # AI生成结果
    generated_body: List[Dict]

    # 校验结果
    validation_result: Optional[Dict]
    validation_errors: List[Dict]

    # 人工审核
    human_review_status: Literal["pending", "approved", "rejected", "modified"]
    human_feedback: Optional[str]
    corrected_body: Optional[List[Dict]]

    # 最终结果
    created_case: Optional[Dict]
    new_usercase_id: Optional[str]

    # 流程控制
    current_step: str
    status: Literal["initialized", "processing", "validating", "reviewing",
                   "approved", "rejected", "completed", "failed"]
    error: Optional[str]
    retry_count: int


# 全局检查点存储（使用内存存储，生产环境可改为 SqliteSaver）
_checkpointer = MemorySaver()


class AutomationWorkflowService:
    """基于 LangGraph 的自动化用例生成工作流服务"""

    def __init__(self, db=None):
        """
        初始化工作流服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.workflow = self._create_workflow()

    def _create_workflow(self):
        """创建 LangGraph 工作流"""

        # 创建状态图
        builder = StateGraph(AutomationCaseState)

        # 添加所有节点
        builder.add_node("load_test_case", self._load_test_case_info)
        builder.add_node("match_scenario", self._match_scenario_by_ai)
        builder.add_node("load_module_config", self._load_module_config)
        builder.add_node("fetch_cases", self._fetch_scene_cases)
        builder.add_node("select_template", self._select_template_by_ai)
        builder.add_node("fetch_details", self._fetch_case_details)
        builder.add_node("generate_data", self._generate_test_data)
        builder.add_node("validate_data", self._validate_generated_data)
        builder.add_node("human_review", self._human_review_node)
        builder.add_node("create_case", self._create_automation_case)

        # 定义流程边（线性流程）
        builder.add_edge(START, "load_test_case")
        builder.add_edge("load_test_case", "match_scenario")
        builder.add_edge("match_scenario", "load_module_config")
        builder.add_edge("load_module_config", "fetch_cases")
        builder.add_edge("fetch_cases", "select_template")
        builder.add_edge("select_template", "fetch_details")
        builder.add_edge("fetch_details", "generate_data")
        builder.add_edge("generate_data", "validate_data")
        builder.add_edge("validate_data", "human_review")

        # 人工审核后的条件分支
        builder.add_conditional_edges(
            "human_review",
            self._decide_after_human_review,
            {
                "create_case": "create_case",
                "regenerate": "generate_data",
                "end": END
            }
        )

        # 创建完成，结束
        builder.add_edge("create_case", END)

        # 使用全局检查点
        return builder.compile(checkpointer=_checkpointer)

    # ===== 节点实现方法 =====

    def _load_test_case_info(self, state: AutomationCaseState) -> AutomationCaseState:
        """节点1: 加载测试用例信息"""
        test_case_id = state.get("test_case_id")
        print(f"[工作流] 步骤1: 加载测试用例 ID={test_case_id}")

        try:
            from app.models.test_case import TestCase
            from app.models.test_point import TestPoint

            # 查询测试用例
            test_case = self.db.query(TestCase).filter(TestCase.id == test_case_id).first()
            if not test_case:
                return {
                    **state,
                    "status": "failed",
                    "error": f"测试用例 ID={test_case_id} 不存在",
                    "current_step": "load_test_case_failed"
                }

            # 查询关联的测试点
            test_point = self.db.query(TestPoint).filter(TestPoint.id == test_case.test_point_id).first()

            # 构建测试用例信息
            test_case_info = {
                "title": test_case.title,
                "description": test_case.description or "",
                "preconditions": test_case.preconditions or "",
                "test_steps": str(test_case.test_steps) if test_case.test_steps else "",
                "expected_result": test_case.expected_result or "",
                "test_type": test_case.test_type or "功能测试",
                "priority": test_case.priority or "P1",
                "business_line": test_point.business_line if test_point else ""
            }

            # 自动生成用例名称（如果未提供）
            name = state.get("name")
            if not name:
                name = f"{test_case.title}_自动化"

            print(f"[工作流] 测试用例加载成功: {test_case.title}")

            return {
                **state,
                "test_case_info": test_case_info,
                "name": name,
                "current_step": "test_case_loaded",
                "status": "processing"
            }
        except Exception as e:
            print(f"[工作流] 加载测试用例失败: {e}")
            return {
                **state,
                "status": "failed",
                "error": f"加载测试用例失败: {str(e)}",
                "current_step": "load_test_case_failed"
            }

    def _match_scenario_by_ai(self, state: AutomationCaseState) -> AutomationCaseState:
        """节点2: AI智能匹配场景（从本地数据库获取场景列表）"""
        print(f"[工作流] 步骤2: AI智能匹配场景")

        # 如果已经有 scene_id，跳过匹配
        if state.get("scene_id"):
            print(f"[工作流] 已指定场景ID: {state['scene_id']}，跳过AI匹配")
            return {
                **state,
                "current_step": "scenario_matched",
                "status": "processing"
            }

        try:
            from app.models.scenario import Scenario
            from app.services.ai_service import get_ai_service

            test_case_info = state.get("test_case_info", {})

            # 从本地数据库获取场景列表
            scenarios = self.db.query(Scenario).filter(
                Scenario.is_active == True
            ).all()

            if not scenarios:
                return {
                    **state,
                    "status": "failed",
                    "error": "数据库中没有可用的测试场景",
                    "current_step": "no_scenarios"
                }

            print(f"[工作流] 从数据库获取到 {len(scenarios)} 个场景")

            # 转换为字典列表供AI分析
            scenarios_for_ai = []
            for s in scenarios:
                scenarios_for_ai.append({
                    'id': s.id,
                    'scenario_code': s.scenario_code,
                    'name': s.name,
                    'description': s.description or '',
                    'business_line': s.business_line or '',
                    'channel': s.channel or '',
                    'module': s.module or ''
                })

            # 使用AI匹配最佳场景
            ai_service = get_ai_service(self.db)
            if not ai_service:
                # AI不可用，使用第一个场景
                default_scenario = scenarios[0]
                print(f"[工作流] AI服务不可用，使用第一个场景: {default_scenario.name}")
                return {
                    **state,
                    "scene_id": default_scenario.scenario_code,
                    "matched_scenario": {
                        "id": default_scenario.id,
                        "name": default_scenario.name,
                        "scenario_code": default_scenario.scenario_code
                    },
                    "current_step": "scenario_matched",
                    "status": "processing"
                }

            # 调用AI选择最佳场景
            selected = ai_service.select_best_scenario(
                test_case_info=test_case_info,
                scenarios=scenarios_for_ai
            )

            if selected:
                print(f"[工作流] AI匹配到场景: {selected.get('name')} (code: {selected.get('scenario_code')})")
                return {
                    **state,
                    "scene_id": selected.get("scenario_code"),
                    "matched_scenario": selected,
                    "current_step": "scenario_matched",
                    "status": "processing"
                }
            else:
                # 默认使用第一个场景
                default_scenario = scenarios[0]
                print(f"[工作流] AI未匹配到场景，使用默认: {default_scenario.name}")
                return {
                    **state,
                    "scene_id": default_scenario.scenario_code,
                    "matched_scenario": {
                        "id": default_scenario.id,
                        "name": default_scenario.name,
                        "scenario_code": default_scenario.scenario_code
                    },
                    "current_step": "scenario_matched",
                    "status": "processing"
                }

        except Exception as e:
            print(f"[工作流] 场景匹配失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                **state,
                "status": "failed",
                "error": f"场景匹配失败: {str(e)}",
                "current_step": "match_scenario_failed"
            }

    def _load_module_config(self, state: AutomationCaseState) -> AutomationCaseState:
        """节点3: 从系统配置读取模块ID"""
        print(f"[工作流] 步骤3: 读取模块配置")

        # 如果已经有 module_id，跳过
        if state.get("module_id"):
            print(f"[工作流] 已指定模块ID: {state['module_id']}")
            return {
                **state,
                "current_step": "module_loaded",
                "status": "processing"
            }

        try:
            from app.models.system_config import SystemConfig

            # 从系统配置读取默认模块ID（使用正确的字段名 config_key）
            config = self.db.query(SystemConfig).filter(
                SystemConfig.config_key == "default_module_id"
            ).first()

            if config and config.config_value:
                print(f"[工作流] 使用系统配置的模块ID: {config.config_value}")
                return {
                    **state,
                    "module_id": config.config_value,
                    "current_step": "module_loaded",
                    "status": "processing"
                }
            else:
                # 使用默认值
                default_module = "1"
                print(f"[工作流] 使用默认模块ID: {default_module}")
                return {
                    **state,
                    "module_id": default_module,
                    "current_step": "module_loaded",
                    "status": "processing"
                }
        except Exception as e:
            print(f"[工作流] 读取模块配置失败: {e}")
            # 使用默认值继续
            return {
                **state,
                "module_id": "1",
                "current_step": "module_loaded",
                "status": "processing"
            }

    def _fetch_scene_cases(self, state: AutomationCaseState) -> AutomationCaseState:
        """节点4: 获取场景用例列表"""
        scene_id = state.get("scene_id")
        print(f"[工作流] 步骤4: 获取场景 {scene_id} 的用例列表")

        try:
            automation_svc = get_automation_service(self.db)
            cases = automation_svc.get_scene_cases(scene_id)

            if not cases:
                return {
                    **state,
                    "status": "failed",
                    "error": f"场景 {scene_id} 没有可用的用例模板",
                    "current_step": "no_cases"
                }

            print(f"[工作流] 获取到 {len(cases)} 个用例模板")

            return {
                **state,
                "scene_cases": cases,
                "current_step": "cases_fetched",
                "status": "processing"
            }
        except Exception as e:
            print(f"[工作流] 获取场景用例失败: {e}")
            return {
                **state,
                "status": "failed",
                "error": f"获取场景用例失败: {str(e)}",
                "current_step": "fetch_cases_failed"
            }

    def _select_template_by_ai(self, state: AutomationCaseState) -> AutomationCaseState:
        """节点5: AI选择最佳模板"""
        print(f"[工作流] 步骤5: AI选择最佳模板")

        cases = state.get("scene_cases", [])
        if not cases:
            return {
                **state,
                "status": "failed",
                "error": "没有可用的用例模板",
                "current_step": "no_templates"
            }

        # 如果只有一个，直接使用
        if len(cases) == 1:
            selected = cases[0]
            print(f"[工作流] 只有一个模板，直接使用: {selected.get('name')}")
            return {
                **state,
                "selected_case": selected,
                "selected_usercase_id": str(selected.get("usercaseId")),
                "current_step": "template_selected",
                "status": "processing"
            }

        try:
            automation_svc = get_automation_service(self.db)
            test_case_info = state.get("test_case_info", {})

            # AI选择最佳模板
            selected = automation_svc.select_best_case_by_ai(
                test_case_info=test_case_info,
                available_cases=cases
            )

            if selected:
                print(f"[工作流] AI选择模板: {selected.get('name')}")
            else:
                selected = cases[0]
                print(f"[工作流] AI未选择，使用第一个: {selected.get('name')}")

            return {
                **state,
                "selected_case": selected,
                "selected_usercase_id": str(selected.get("usercaseId")),
                "current_step": "template_selected",
                "status": "processing"
            }
        except Exception as e:
            print(f"[工作流] AI选择模板失败: {e}")
            # 降级使用第一个
            selected = cases[0]
            return {
                **state,
                "selected_case": selected,
                "selected_usercase_id": str(selected.get("usercaseId")),
                "current_step": "template_selected",
                "status": "processing"
            }

    def _fetch_case_details(self, state: AutomationCaseState) -> AutomationCaseState:
        """节点6: 获取用例详情和字段元数据"""
        usercase_id = state.get("selected_usercase_id")
        print(f"[工作流] 步骤6: 获取用例 {usercase_id} 的详情")

        try:
            automation_svc = get_automation_service(self.db)

            # 获取用例详情
            case_detail = automation_svc.get_case_detail(usercase_id)
            if not case_detail:
                return {
                    **state,
                    "status": "failed",
                    "error": f"获取用例详情失败: {usercase_id}",
                    "current_step": "fetch_details_failed"
                }

            # 提取字段定义
            case_define = case_detail.get("caseDefine", {})
            header_fields = case_define.get("header", [])
            circulation = state["selected_case"].get("circulation", [])

            print(f"[工作流] 提取到 {len(header_fields)} 个字段定义")

            # 获取字段元数据（枚举值+联动规则）
            metadata_svc = FieldMetadataService(automation_svc)
            field_metadata = metadata_svc.fetch_field_metadata(state["scene_id"])
            linkage_rules = metadata_svc.extract_linkage_rules(field_metadata)

            print(f"[工作流] 获取到 {len(field_metadata.get('fields', []))} 个字段元数据")

            return {
                **state,
                "case_detail": case_detail,
                "header_fields": header_fields,
                "circulation": circulation,
                "field_metadata": field_metadata,
                "linkage_rules": linkage_rules,
                "current_step": "details_fetched",
                "status": "processing"
            }
        except Exception as e:
            print(f"[工作流] 获取用例详情失败: {e}")
            return {
                **state,
                "status": "failed",
                "error": f"获取用例详情失败: {str(e)}",
                "current_step": "fetch_details_failed"
            }

    def _generate_test_data(self, state: AutomationCaseState) -> AutomationCaseState:
        """节点7: AI生成测试数据"""
        retry_count = state.get("retry_count", 0)
        print(f"[工作流] 步骤7: AI生成测试数据 (尝试 {retry_count + 1}/3)")

        try:
            automation_svc = get_automation_service(self.db)

            # 提取示例数据
            example_body = None
            if state.get("case_detail") and state["case_detail"].get("caseDefine"):
                template_body = state["case_detail"]["caseDefine"].get("body", [])
                if template_body:
                    example_body = template_body[0]

            # 调用AI生成
            generated_body = automation_svc.generate_case_body_by_ai(
                header_fields=state["header_fields"],
                test_case_info=state.get("test_case_info"),
                circulation=state.get("circulation"),
                example_body=example_body
            )

            if not generated_body:
                print(f"[工作流] AI未能生成测试数据")
                return {
                    **state,
                    "status": "failed",
                    "error": "AI未能生成测试数据",
                    "retry_count": retry_count + 1,
                    "current_step": "generate_failed"
                }

            print(f"[工作流] AI生成了 {len(generated_body)} 条测试数据")

            return {
                **state,
                "generated_body": generated_body,
                "current_step": "data_generated",
                "status": "processing"
            }
        except Exception as e:
            print(f"[工作流] AI生成测试数据失败: {e}")
            return {
                **state,
                "status": "failed",
                "error": f"AI生成测试数据失败: {str(e)}",
                "retry_count": retry_count + 1,
                "current_step": "generate_failed"
            }

    def _validate_generated_data(self, state: AutomationCaseState) -> AutomationCaseState:
        """节点8: 数据校验"""
        print(f"[工作流] 步骤8: 校验生成的测试数据")

        try:
            # 如果没有元数据，跳过校验
            if not state.get("field_metadata") or not state["field_metadata"].get("fields"):
                print(f"[工作流] 无字段元数据，跳过校验")
                return {
                    **state,
                    "validation_result": {
                        "total": len(state.get("generated_body", [])),
                        "valid_count": len(state.get("generated_body", [])),
                        "invalid_count": 0,
                        "total_errors": 0,
                        "results": []
                    },
                    "validation_errors": [],
                    "current_step": "data_validated",
                    "status": "processing"
                }

            validator = BodyValidator(state["field_metadata"])
            validation_result = validator.validate_all(state["generated_body"])

            # 提取所有错误
            errors = []
            for result in validation_result["results"]:
                if result["validation"]["errors"]:
                    errors.extend(result["validation"]["errors"])

            print(f"[工作流] 校验完成: {validation_result['valid_count']}/{validation_result['total']} 条有效")

            return {
                **state,
                "validation_result": validation_result,
                "validation_errors": errors,
                "current_step": "data_validated",
                "status": "processing"
            }
        except Exception as e:
            print(f"[工作流] 数据校验失败: {e}")
            return {
                **state,
                "validation_result": None,
                "validation_errors": [],
                "current_step": "validation_error",
                "status": "processing"
            }

    def _human_review_node(self, state: AutomationCaseState) -> AutomationCaseState:
        """节点9: 人工审核 - 使用 interrupt 暂停工作流"""
        print(f"[工作流] 步骤9: 等待人工审核")

        # 准备审核数据
        review_data = {
            "generated_body": state.get("generated_body", []),
            "validation_result": state.get("validation_result"),
            "field_metadata": state.get("field_metadata"),
            "header_fields": state.get("header_fields", []),
            "name": state.get("name"),
            "matched_scenario": state.get("matched_scenario"),
            "test_case_info": state.get("test_case_info"),
            "action": "请审核AI生成的测试数据"
        }

        # 使用 interrupt 暂停工作流，等待人工审核
        # interrupt 返回值是用户通过 Command(resume=...) 提供的数据
        human_response = interrupt(review_data)

        print(f"[工作流] 收到人工审核结果: {human_response.get('review_status')}")

        # 解析人工审核结果
        review_status = human_response.get("review_status", "approved")
        corrected_body = human_response.get("corrected_body")
        feedback = human_response.get("feedback", "")

        # 如果有修正数据，使用修正数据
        final_body = corrected_body if corrected_body else state.get("generated_body", [])

        return {
            **state,
            "human_review_status": review_status,
            "human_feedback": feedback,
            "generated_body": final_body,
            "current_step": "human_reviewed",
            "status": review_status
        }

    def _decide_after_human_review(self, state: AutomationCaseState) -> str:
        """条件判断: 人工审核后的走向"""
        review_status = state.get("human_review_status", "pending")
        status = state.get("status", "unknown")

        if review_status == "rejected":
            retry_count = state.get("retry_count", 0)
            if retry_count < 3:
                print(f"[工作流] 人工拒绝，重新生成 (第 {retry_count + 1} 次)")
                return "regenerate"
            else:
                print(f"[工作流] 重试次数已达上限")
                return "end"

        if review_status in ["approved", "modified"]:
            print(f"[工作流] 人工审核通过，创建用例")
            return "create_case"

        if status == "failed":
            print(f"[工作流] 状态失败，结束流程")
            return "end"

        # 默认创建用例
        return "create_case"

    def _create_automation_case(self, state: AutomationCaseState) -> AutomationCaseState:
        """节点10: 创建自动化用例"""
        print(f"[工作流] 步骤10: 创建自动化用例")

        try:
            automation_svc = get_automation_service(self.db)

            # 更新 case_detail 的 body
            case_detail = state["case_detail"].copy()
            if "caseDefine" not in case_detail:
                case_detail["caseDefine"] = {}
            case_detail["caseDefine"]["body"] = state["generated_body"]

            # 准备 tags
            tags_data = []
            if state.get("circulation"):
                for circ in state["circulation"]:
                    tags_data.append(f"{circ.get('name', '')}({circ.get('vargroup', '')})")
            tags = json.dumps(tags_data, ensure_ascii=False) if tags_data else "[]"

            # 创建用例
            case_data = automation_svc.create_case_and_body(
                name=state["name"],
                module_id=state["module_id"],
                scene_id=state["scene_id"],
                template_case_detail=case_detail,
                scenario_type=state.get("scenario_type", "API"),
                description=state.get("description", ""),
                tags=tags
            )

            if case_data:
                new_id = case_data.get("id") or case_data.get("usercaseId")
                print(f"[工作流] 用例创建成功! ID: {new_id}")
                return {
                    **state,
                    "created_case": case_data,
                    "new_usercase_id": str(new_id) if new_id else None,
                    "current_step": "case_created",
                    "status": "completed"
                }
            else:
                return {
                    **state,
                    "status": "failed",
                    "error": "创建用例返回空数据",
                    "current_step": "create_case_failed"
                }
        except Exception as e:
            print(f"[工作流] 创建用例失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                **state,
                "status": "failed",
                "error": f"创建用例失败: {str(e)}",
                "current_step": "create_case_failed"
            }

    # ===== 公共方法 =====

    def start_workflow(self, initial_state: Dict, thread_id: str) -> Dict:
        """
        启动工作流

        Args:
            initial_state: 初始状态
            thread_id: 线程ID

        Returns:
            工作流当前状态（可能在 human_review 暂停）
        """
        print(f"[工作流] 启动工作流，线程ID: {thread_id}")

        config = {"configurable": {"thread_id": thread_id}}

        # 初始化状态
        state = {
            **initial_state,
            "status": "initialized",
            "current_step": "start",
            "retry_count": 0,
            "human_review_status": "pending",
            "generated_body": [],
            "validation_errors": [],
            "scene_cases": [],
            "header_fields": [],
            "circulation": [],
            "linkage_rules": []
        }

        # 执行工作流（会在 human_review 节点的 interrupt 处暂停）
        current_state = None
        interrupt_data = None

        try:
            for event in self.workflow.stream(state, config, stream_mode="values"):
                current_state = event
                print(f"[工作流] 当前步骤: {current_state.get('current_step')}")

            # 检查是否有中断
            snapshot = self.workflow.get_state(config)
            if snapshot.next:
                # 工作流在某个节点暂停了（interrupt）
                print(f"[工作流] 工作流在节点暂停: {snapshot.next}")
                if hasattr(snapshot, 'tasks') and snapshot.tasks:
                    for task in snapshot.tasks:
                        if hasattr(task, 'interrupts') and task.interrupts:
                            interrupt_data = task.interrupts[0].value
                            print(f"[工作流] 获取到 interrupt 数据")

            if interrupt_data:
                return {
                    **current_state,
                    "status": "reviewing",
                    "current_step": "awaiting_human_review",
                    "interrupt_data": interrupt_data
                }

            return current_state or state

        except Exception as e:
            print(f"[工作流] 执行异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                **state,
                "status": "failed",
                "error": f"工作流执行异常: {str(e)}",
                "current_step": "workflow_error"
            }

    def resume_workflow(
        self,
        thread_id: str,
        review_status: str,
        corrected_body: Optional[List[Dict]] = None,
        feedback: Optional[str] = None
    ) -> Dict:
        """
        恢复工作流执行（提交人工审核结果）

        Args:
            thread_id: 线程ID
            review_status: 审核状态 (approved/modified/rejected)
            corrected_body: 修正后的数据
            feedback: 反馈意见

        Returns:
            最终状态
        """
        print(f"[工作流] 恢复工作流执行: {review_status}")

        config = {"configurable": {"thread_id": thread_id}}

        # 构建人工审核结果
        human_response = {
            "review_status": review_status,
            "corrected_body": corrected_body,
            "feedback": feedback
        }

        try:
            # 使用 Command(resume=...) 恢复工作流
            final_state = None
            for event in self.workflow.stream(
                Command(resume=human_response),
                config,
                stream_mode="values"
            ):
                final_state = event
                print(f"[工作流] 当前步骤: {final_state.get('current_step')}")

            print(f"[工作流] 执行完成，最终状态: {final_state.get('status') if final_state else 'unknown'}")
            return final_state

        except Exception as e:
            print(f"[工作流] 恢复执行异常: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "failed",
                "error": f"恢复执行异常: {str(e)}",
                "current_step": "resume_error"
            }

    def get_state(self, thread_id: str) -> Dict:
        """
        获取当前状态

        Args:
            thread_id: 线程ID

        Returns:
            当前状态
        """
        config = {"configurable": {"thread_id": thread_id}}

        try:
            state_snapshot = self.workflow.get_state(config)
            if state_snapshot and state_snapshot.values:
                state = dict(state_snapshot.values)

                # 检查是否有中断
                if state_snapshot.next:
                    state["status"] = "reviewing"
                    state["current_step"] = "awaiting_human_review"

                    # 提取 interrupt 数据
                    if hasattr(state_snapshot, 'tasks') and state_snapshot.tasks:
                        for task in state_snapshot.tasks:
                            if hasattr(task, 'interrupts') and task.interrupts:
                                state["interrupt_data"] = task.interrupts[0].value

                return state
            return {}
        except Exception as e:
            print(f"[工作流] 获取状态失败: {e}")
            return {}
