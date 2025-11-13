import operator
import time
from typing import List, Dict, Any, TypedDict, Annotated

from typing_extensions import TypedDict as ExtTypedDict
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END, START
from sqlalchemy.orm import Session

from app.core.config import settings


class GraphState(ExtTypedDict):
    """LangGraph 状态定义 - 使用 Annotated 类型支持状态更新"""
    requirement_text: str
    test_points: Annotated[List[Dict[str, Any]], operator.add]
    user_feedback: str
    test_cases: Annotated[List[Dict[str, Any]], operator.add]
    current_step: str


class AIService:
    """AI 服务 - 使用 LangGraph 生成测试点和用例"""

    def __init__(self, db: Session = None, model_config_id: int = None):
        """
        初始化 AI 服务

        Args:
            db: 数据库会话
            model_config_id: 指定使用的模型配置 ID,如果为 None 则使用默认模型
        """
        self.db = db

        # 获取模型配置
        model_config = self._get_model_config(model_config_id)

        # LangChain 1.0+ API: 使用 api_key 和 base_url 参数
        # 处理 temperature: 如果为空字符串或 None,使用默认值 1.0
        temp_value = model_config.get("temperature", "1.0")
        temperature = float(temp_value) if temp_value and str(temp_value).strip() else 1.0

        self.llm = ChatOpenAI(
            model=model_config["model_name"],
            api_key=model_config["api_key"],
            base_url=model_config["api_base"] if model_config["api_base"] else None,
            temperature=temperature,
            max_tokens=model_config.get("max_tokens")
        )
        self.embeddings = OpenAIEmbeddings(
            api_key=model_config["api_key"],
            base_url=model_config["api_base"] if model_config["api_base"] else None
        )

    def _get_model_config(self, model_config_id: int = None) -> Dict[str, Any]:
        """
        获取模型配置

        Args:
            model_config_id: 模型配置 ID,如果为 None 则使用默认模型

        Returns:
            模型配置字典
        """
        # 如果有数据库连接,尝试从数据库获取配置
        if self.db:
            try:
                from app.models.model_config import ModelConfig

                if model_config_id:
                    # 使用指定的模型配置
                    config = self.db.query(ModelConfig).filter(
                        ModelConfig.id == model_config_id,
                        ModelConfig.is_active == True
                    ).first()
                else:
                    # 使用默认模型配置
                    config = self.db.query(ModelConfig).filter(
                        ModelConfig.is_default == True,
                        ModelConfig.is_active == True
                    ).first()

                if config:
                    # 处理 temperature: 如果为空字符串或 None,使用默认值
                    temp = config.temperature
                    if not temp or (isinstance(temp, str) and not temp.strip()):
                        temp = "1.0"

                    return {
                        "api_key": config.api_key,
                        "api_base": config.api_base,
                        "model_name": config.model_name,
                        "temperature": temp,
                        "max_tokens": config.max_tokens
                    }
            except Exception as e:
                print(f"[WARNING] 从数据库获取模型配置失败: {e}")

        # 回退到环境变量配置
        return {
            "api_key": settings.OPENAI_API_KEY,
            "api_base": settings.OPENAI_API_BASE,
            "model_name": settings.MODEL_NAME,
            "temperature": "0.7",
            "max_tokens": None
        }
        
    def get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入向量"""
        return self.embeddings.embed_query(text)

    def _get_prompt_from_db(self, key: str, default: str) -> str:
        """从数据库获取 Prompt 配置"""
        if not self.db:
            return default

        try:
            from app.models.system_config import SystemConfig
            config = self.db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
            if config:
                return config.config_value
        except Exception as e:
            print(f"[WARNING] 获取 Prompt 配置失败: {str(e)}")

        return default
    
    def extract_test_points(
        self,
        requirement_text: str,
        user_feedback: str = None,
        allow_fallback: bool = True,
    ) -> List[Dict[str, Any]]:
        """从需求文档中提取测试点"""

        try:
            if not requirement_text or not requirement_text.strip():
                raise ValueError("Requirement text is empty")

            max_length = max(settings.TEST_POINT_MAX_INPUT_CHARS, 1000)
            if len(requirement_text) > max_length:
                print(
                    f"[WARNING] 需求文本过长 ({len(requirement_text)} 字符)，截取前 {max_length} 字符"
                )
                requirement_text = requirement_text[:max_length] + "..."

            default_prompt = """你是一个专业的保险行业测试专家。请从需求文档中识别所有测试点。

测试点应该包括：
1. 功能性测试点
2. 边界条件测试点
3. 异常情况测试点
4. 业务规则验证点

请以JSON格式返回测试点列表，每个测试点包含：
- title: 测试点标题
- description: 详细描述
- category: 分类（功能/边界/异常/业务规则）
- priority: 优先级（high/medium/low）
- business_line: 业务线（contract-契约/preservation-保全/claim-理赔），根据需求内容判断属于哪个业务线

{feedback_instruction}"""

            system_prompt = self._get_prompt_from_db("TEST_POINT_PROMPT", default_prompt)

            prompt_template = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    ("user", "需求文档内容：\n{requirement_text}"),
                ]
            )

            feedback_instruction = ""
            if user_feedback:
                feedback_instruction = (
                    f"\n用户反馈意见：{user_feedback}\n请根据用户反馈调整测试点。"
                )

            messages = prompt_template.format_messages(
                requirement_text=requirement_text,
                feedback_instruction=feedback_instruction,
            )

            print("[INFO] 调用 OpenAI API...")
            retries = max(settings.AI_MAX_RETRIES, 1)
            delay = max(settings.AI_RETRY_INTERVAL, 1)
            response = None
            last_error = None
            for attempt in range(1, retries + 1):
                try:
                    response = self.llm.invoke(messages)
                    break
                except Exception as invoke_error:
                    last_error = invoke_error
                    print(
                        f"[WARNING] OpenAI API 调用失败（第 {attempt}/{retries} 次）：{invoke_error}"
                    )
                    if attempt < retries:
                        time.sleep(delay)
            if response is None:
                raise last_error or RuntimeError("OpenAI 响应为空")
            print(f"[INFO] OpenAI API 响应成功，内容长度: {len(response.content)}")

            import json

            content = response.content
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                test_points = json.loads(json_str)
                print(f"[INFO] 成功解析 {len(test_points)} 个测试点")
                return test_points

            print("[WARNING] 未找到 JSON 数组，尝试解析整个响应")
            test_points = json.loads(content)
            if isinstance(test_points, list):
                return test_points

            raise ValueError("AI 响应格式不正确，未返回测试点列表")

        except Exception as e:
            print(f"[ERROR] AI 提取测试点失败: {str(e)}")
            import traceback

            traceback.print_exc()
            if allow_fallback:
                print("[WARNING] 使用示例数据")
                return [
                    {
                        "title": "功能测试点示例",
                        "description": "这是一个示例测试点，AI 解析失败时显示",
                        "category": "功能",
                        "priority": "high",
                        "business_line": "contract",
                    },
                    {
                        "title": "边界测试点示例",
                        "description": "请检查 OpenAI API Key 配置和网络连接",
                        "category": "边界",
                        "priority": "medium",
                        "business_line": "preservation",
                    },
                ]
            raise

    def generate_test_cases(self, test_point: Dict[str, Any], requirement_context: str = "") -> List[Dict[str, Any]]:
        """根据测试点生成测试用例"""

        # 根据业务线选择对应的 Prompt
        business_line = test_point.get('business_line', '')

        default_prompt = """你是一个专业的测试用例设计专家。请根据测试点生成详细的测试用例。

测试用例应该包含：
- title: 用例标题
- description: 用例描述
- preconditions: 前置条件
- test_steps: 测试步骤（数组格式，每步包含 step, action, expected）
- expected_result: 预期结果
- priority: 优先级
- test_type: 测试类型

请以JSON格式返回测试用例列表。"""

        # 根据业务线选择对应的 Prompt 配置键
        # 支持 'contract' 或 'contract-契约' 等格式
        if business_line and ('contract' in business_line.lower() or '契约' in business_line):
            prompt_key = "CONTRACT_TEST_CASE_PROMPT"
            print(f"[INFO] 使用契约业务线 Prompt 生成测试用例 (business_line={business_line})")
        elif business_line and ('preservation' in business_line.lower() or '保全' in business_line):
            prompt_key = "PRESERVATION_TEST_CASE_PROMPT"
            print(f"[INFO] 使用保全业务线 Prompt 生成测试用例 (business_line={business_line})")
        elif business_line and ('claim' in business_line.lower() or '理赔' in business_line):
            prompt_key = "CLAIM_TEST_CASE_PROMPT"
            print(f"[INFO] 使用理赔业务线 Prompt 生成测试用例 (business_line={business_line})")
        else:
            prompt_key = "TEST_CASE_PROMPT"
            print(f"[INFO] 使用默认 Prompt 生成测试用例 (business_line={business_line})")

        system_prompt = self._get_prompt_from_db(prompt_key, default_prompt)

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", """测试点信息：
标题：{title}
描述：{description}
分类：{category}

需求上下文：
{context}

请生成 2-3 个相关的测试用例。
""")
        ])
        
        messages = prompt_template.format_messages(
            title=test_point.get('title', ''),
            description=test_point.get('description', ''),
            category=test_point.get('category', ''),
            context=requirement_context
        )
        
        response = self.llm.invoke(messages)
        
        # 解析响应（简化处理）
        try:
            import json
            content = response.content
            start = content.find('[')
            end = content.rfind(']') + 1
            if start != -1 and end > start:
                test_cases = json.loads(content[start:end])
                return test_cases
        except:
            pass
        
        # 返回示例数据
        return [
            {
                "title": f"{test_point.get('title', '')} - 正常流程",
                "description": "验证正常业务流程",
                "preconditions": "系统正常运行，用户已登录",
                "test_steps": [
                    {"step": 1, "action": "打开功能页面", "expected": "页面正常显示"},
                    {"step": 2, "action": "输入有效数据", "expected": "数据验证通过"},
                    {"step": 3, "action": "提交表单", "expected": "操作成功"}
                ],
                "expected_result": "功能正常执行",
                "priority": test_point.get('priority', 'medium'),
                "test_type": "functional"
            }
        ]
    
    def create_workflow(self):
        """创建 LangGraph 工作流 - 使用 LangGraph 1.0+ API"""

        workflow = StateGraph(GraphState)

        def analyze_requirement(state: GraphState) -> Dict[str, Any]:
            """分析需求节点 - 返回状态更新字典"""
            test_points = self.extract_test_points(
                state["requirement_text"],
                state.get("user_feedback", "")
            )
            return {
                "test_points": test_points,
                "current_step": "test_points_generated"
            }

        def generate_cases(state: GraphState) -> Dict[str, Any]:
            """生成测试用例节点 - 返回状态更新字典"""
            test_cases = []
            for test_point in state.get("test_points", []):
                cases = self.generate_test_cases(test_point, state["requirement_text"])
                test_cases.extend(cases)
            return {
                "test_cases": test_cases,
                "current_step": "test_cases_generated"
            }

        # 添加节点
        workflow.add_node("analyze", analyze_requirement)
        workflow.add_node("generate", generate_cases)

        # 添加边 - LangGraph 1.0+ 使用 START 代替 set_entry_point
        workflow.add_edge(START, "analyze")
        workflow.add_edge("analyze", "generate")
        workflow.add_edge("generate", END)

        return workflow.compile()


# 全局实例（用于不需要 Prompt 配置的场景）
ai_service = AIService()


def get_ai_service(db: Session = None, model_config_id: int = None) -> AIService:
    """
    获取 AI 服务实例

    Args:
        db: 数据库会话（支持 Prompt 配置和模型配置）
        model_config_id: 指定使用的模型配置 ID,如果为 None 则使用默认模型

    Returns:
        AIService 实例
    """
    return AIService(db=db, model_config_id=model_config_id)

