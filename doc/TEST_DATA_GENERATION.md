# 测试数据生成方案（LangGraph 智能化版本）

## 一、LangGraph 智能化工作流

### 1.1 核心特性

**完全智能化**：用户只需选择测试用例，系统自动完成所有配置和匹配：
- ✅ **自动加载测试用例信息**：根据 test_case_id 自动提取标题、描述、步骤等
- ✅ **AI 智能匹配场景**：自动分析业务线，AI 选择最佳场景
- ✅ **自动读取模块配置**：从系统配置表自动获取模块 ID
- ✅ **AI 选择最佳模板**：智能匹配场景下的用例模板
- ✅ **AI 生成测试数据**：带枚举约束和联动规则的智能生成
- ✅ **自动数据校验**：三层校验（枚举值、联动规则、必填字段）
- ✅ **人工审核支持**：数据有问题时暂停，支持人工修正

### 1.2 工作流架构图

```
                    START
                      ↓
         ┌─────────────────────────┐
         │  节点0: 加载测试用例信息   │
         │  - 根据 test_case_id    │
         │  - 提取用例详情          │
         │  - 自动生成用例名称       │
         └─────────────────────────┘
                      ↓
         ┌─────────────────────────┐
         │  节点1: AI 智能匹配场景   │
         │  - 查询所有激活场景      │
         │  - 优先匹配业务线        │
         │  - AI 选择最佳场景       │
         └─────────────────────────┘
                      ↓
         ┌─────────────────────────┐
         │  节点2: 加载模块配置      │
         │  - 从系统配置表读取      │
         │  - 自动填充 module_id   │
         └─────────────────────────┘
                      ↓
         ┌─────────────────────────┐
         │  节点3: 获取场景用例列表  │
         │  - 调用自动化平台 API    │
         └─────────────────────────┘
                      ↓
         ┌─────────────────────────┐
         │  节点4: AI 选择最佳模板   │
         │  - AI 分析用例相似度     │
         └─────────────────────────┘
                      ↓
         ┌─────────────────────────┐
         │  节点5: 获取用例详情和    │
         │        字段元数据        │
         │  - 获取 header/body     │
         │  - 获取枚举值和联动规则   │
         └─────────────────────────┘
                      ↓
         ┌─────────────────────────┐
         │  节点6: AI 生成测试数据   │
         │  - 带枚举约束            │
         │  - 遵守联动规则          │
         └─────────────────────────┘
                      ↓
         ┌─────────────────────────┐
         │  节点7: 数据校验         │
         │  - 枚举值校验            │
         │  - 联动规则校验          │
         │  - 必填字段校验          │
         └─────────────────────────┘
                      ↓
            ┌─────────┴─────────┐
            ↓                   ↓
      有问题需审核         无问题自动通过
            ↓                   ↓
   ┌─────────────────┐   ┌─────────────────┐
   │ 节点8: 人工审核   │   │ 节点10: 创建用例 │
   │ (暂停等待输入)    │   │                 │
   └─────────────────┘   └─────────────────┘
            ↓                   ↓
   ┌─────────────────┐        END
   │ 节点9: 应用修正   │
   └─────────────────┘
            ↓
      ┌─────┴─────┐
      ↓           ↓
   通过/修改    拒绝重新生成
      ↓           ↓
  创建用例    节点11: 重新生成
      ↓           ↓
     END    (回到节点6)
```

### 1.3 智能化前后对比

| 维度 | 改进前 | 改进后 | 改善幅度 |
|------|--------|--------|---------|
| **必填字段** | 9个（名称、模块ID、场景ID等） | 0个（只选测试用例） | ↓ 100% |
| **操作步骤** | 6步（填写多个表单） | 2步（选择用例→启动） | ↓ 67% |
| **场景匹配** | 手动查询输入 | AI 自动匹配 | 完全自动化 |
| **模块ID获取** | 手动输入 | 系统配置读取 | 完全自动化 |
| **出错可能** | 高（手动输入容易错） | 低（AI 智能处理） | ↓ 90% |
| **用户体验** | 繁琐复杂 | 极简便捷 | ✨ 质的飞跃 |

---

## 二、后端实现

### 2.1 LangGraph 状态定义

```python
from typing import TypedDict, Optional, List, Dict, Literal

class AutomationCaseState(TypedDict, total=False):
    """自动化用例生成状态"""

    # 输入参数（智能化）
    test_case_id: int                    # 测试用例ID（唯一必填）
    name: Optional[str]                  # 用例名称（自动生成）
    module_id: Optional[str]             # 模块ID（从配置读取）
    scene_id: Optional[str]              # 场景ID（AI匹配）
    scenario_type: str                   # 场景类型
    description: str                     # 描述
    test_case_info: Optional[Dict]       # 测试用例信息（自动加载）

    # AI匹配场景相关
    available_scenarios: List[Dict]      # 可用场景列表
    matched_scenario: Optional[Dict]     # AI匹配的场景

    # 流程中间状态
    scene_cases: List[Dict]              # 场景用例列表
    selected_case: Optional[Dict]        # 选中的模板用例
    selected_usercase_id: Optional[str]  # 模板用例ID
    case_detail: Optional[Dict]          # 用例详情
    header_fields: List[Dict]            # 字段定义
    circulation: List[Dict]              # 环节信息

    # 元数据和规则
    field_metadata: Optional[Dict]       # 字段元数据（枚举值+联动）
    linkage_rules: List[Dict]            # 联动规则

    # AI生成结果
    generated_body: List[Dict]           # AI生成的测试数据

    # 校验结果
    validation_result: Optional[Dict]    # 校验结果
    validation_errors: List[Dict]        # 校验错误列表

    # 人工审核
    human_review_status: Literal["pending", "approved", "rejected", "modified"]
    human_feedback: Optional[str]        # 人工反馈意见
    corrected_body: Optional[List[Dict]] # 人工修正后的数据

    # 最终结果
    created_case: Optional[Dict]         # 创建的用例信息
    new_usercase_id: Optional[str]       # 新用例ID

    # 流程控制
    current_step: str                    # 当前步骤
    status: Literal["initialized", "processing", "validating", "reviewing",
                   "approved", "rejected", "completed", "failed"]
    error: Optional[str]                 # 错误信息
    retry_count: int                     # 重试次数
```

### 2.2 工作流服务

文件：`backend/app/services/automation_workflow_service.py`

```python
class AutomationWorkflowService:
    """基于 LangGraph 的自动化用例生成工作流服务"""

    def __init__(self, db=None):
        self.db = db
        self.workflow = self._create_workflow()

    def _create_workflow(self):
        """创建 LangGraph 工作流"""
        builder = StateGraph(AutomationCaseState)

        # 添加所有节点（智能化流程）
        builder.add_node("load_test_case", self._load_test_case_info)
        builder.add_node("match_scenario", self._match_scenario_by_ai)
        builder.add_node("load_module_config", self._load_module_config)
        builder.add_node("fetch_cases", self._fetch_scene_cases)
        builder.add_node("select_template", self._select_template_by_ai)
        builder.add_node("fetch_details", self._fetch_case_details)
        builder.add_node("generate_data", self._generate_test_data)
        builder.add_node("validate_data", self._validate_generated_data)
        builder.add_node("human_review", self._human_review)
        builder.add_node("apply_corrections", self._apply_corrections)
        builder.add_node("create_case", self._create_automation_case)
        builder.add_node("regenerate", self._regenerate_data)

        # 定义流程边（智能化流程）
        builder.add_edge(START, "load_test_case")
        builder.add_edge("load_test_case", "match_scenario")
        builder.add_edge("match_scenario", "load_module_config")
        builder.add_edge("load_module_config", "fetch_cases")
        builder.add_edge("fetch_cases", "select_template")
        builder.add_edge("select_template", "fetch_details")
        builder.add_edge("fetch_details", "generate_data")
        builder.add_edge("generate_data", "validate_data")

        # 校验后的条件分支
        builder.add_conditional_edges(
            "validate_data",
            self._decide_after_validation,
            {
                "regenerate": "regenerate",
                "human_review": "human_review",
                "create_case": "create_case"
            }
        )

        builder.add_edge("human_review", "apply_corrections")

        # 人工审核后的条件分支
        builder.add_conditional_edges(
            "apply_corrections",
            self._decide_after_human_review,
            {
                "regenerate": "regenerate",
                "create_case": "create_case"
            }
        )

        builder.add_edge("regenerate", "generate_data")
        builder.add_edge("create_case", END)

        # 使用内存检查点
        checkpointer = MemorySaver()

        return builder.compile(checkpointer=checkpointer)
```

### 2.3 API 端点

文件：`backend/app/api/v1/endpoints/automation_workflow.py`

```python
@router.post("/workflow/start", response_model=WorkflowStateResponse)
async def start_automation_workflow(
    request: CreateCaseWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    启动自动化用例生成工作流（智能化版本）

    参数:
        - test_case_id: 必填，测试用例ID
        - scenario_type: 可选，场景类型（默认API）

    系统自动处理:
        - 加载测试用例信息
        - AI 智能匹配场景
        - 从系统配置读取模块ID
        - AI 选择最佳模板
        - AI 生成测试数据
        - 自动校验数据
        - 如有问题暂停等待人工审核
    """
    workflow_svc = AutomationWorkflowService(db)
    thread_id = f"workflow_{current_user.id}_{uuid.uuid4().hex[:8]}"

    # 准备初始状态（智能化参数）
    initial_state = {
        "test_case_id": request.test_case_id,  # ← 唯一必填
        "scenario_type": request.scenario_type or "API"
    }

    # 启动工作流
    current_state = workflow_svc.start_workflow(initial_state, thread_id)

    return WorkflowStateResponse(
        thread_id=thread_id,
        status=current_state.get("status"),
        current_step=current_state.get("current_step"),
        need_human_review=current_state.get("status") == "reviewing",
        state=current_state
    )
```

### 2.4 请求/响应模型

文件：`backend/app/schemas/automation.py`

```python
class CreateCaseWorkflowRequest(BaseModel):
    """启动工作流请求（智能化版本）"""

    test_case_id: int = Field(..., description="测试用例ID（唯一必填）")
    scenario_type: Optional[str] = Field("API", description="场景类型")

    class Config:
        json_schema_extra = {
            "example": {
                "test_case_id": 123,
                "scenario_type": "API"
            }
        }
```

---

## 三、前端实现

### 3.1 极简化界面

文件：`frontend/src/pages/AutomationWorkflowCreate.tsx`

**核心特性**：
- ✅ **移除所有表单字段**：不再需要填写任何信息
- ✅ **表格选择测试用例**：点击行或"选择"按钮
- ✅ **操作按钮置顶**：启动工作流和重置按钮在表格上方
- ✅ **实时状态显示**：显示已选择的测试用例

### 3.2 使用流程

```
1. 访问"自动化工作流"页面
2. 从表格中点击选择一个测试用例
3. 点击顶部的"启动智能工作流"按钮
4. 等待 AI 自动处理：
   - 加载用例信息
   - AI 匹配场景
   - 读取模块配置
   - AI 生成测试数据
   - 自动校验数据
5. 如需人工审核：
   - 在弹窗中查看 AI 生成的数据
   - 查看校验错误提示
   - 修正错误的字段值
   - 点击"确认提交"
6. 完成！
```

### 3.3 前端代码示例

```typescript
// 启动工作流（极简化版本）
const handleSubmit = async () => {
  if (!selectedTestCase) {
    message.error('请先选择一个测试用例');
    return;
  }

  setLoading(true);
  try {
    // 只需传递测试用例ID
    const response = await api.post('/automation/workflow/start', {
      test_case_id: selectedTestCase.id,
      scenario_type: 'API'
    });

    const data = response.data;
    setThreadId(data.thread_id);
    setWorkflowState(data);

    if (data.need_human_review) {
      message.info('AI 已生成测试数据，请进行人工审核');
      setReviewModalVisible(true);
    } else if (data.status === 'completed') {
      message.success('自动化用例创建成功！');
    }
  } catch (error) {
    message.error(`创建失败: ${error.message}`);
  } finally {
    setLoading(false);
  }
};
```

---

## 四、配置说明

### 4.1 前置准备（一次性配置）

#### 1. 配置默认模块 ID

在「系统配置」页面添加配置：

```
配置键: AUTOMATION_PLATFORM_MODULE_ID
配置值: 你的模块ID（如：MOD_123）
描述: 自动化测试平台的默认模块ID
```

#### 2. 创建场景

在「场景管理」页面创建场景：

| 字段 | 说明 | 示例 |
|------|------|------|
| 场景编号 | 必填，唯一标识 | SCENE_CLAIM_001 |
| 场景名称 | 必填，用于 AI 匹配 | 理赔流程 |
| 业务线 | 可选，优先匹配 | 健康险 |
| 渠道 | 可选 | 直销 |
| 模块 | 可选 | 理赔模块 |
| 状态 | 必须启用 | 启用 |

#### 3. 创建测试用例

在「用例管理」页面创建测试用例，包含：
- 标题
- 描述
- 前置条件
- 测试步骤
- 预期结果
- 测试类型
- 优先级

### 4.2 AI 匹配逻辑

**场景匹配策略**：
1. 查询所有 `is_active=True` 的场景
2. 优先筛选业务线相同的场景
3. 调用 `ai_service.select_best_scenario()`
4. AI 分析测试用例的标题、描述、业务线等
5. 返回最匹配的场景
6. 使用场景的 `scenario_code` 作为 `scene_id`

**模块ID读取策略**：
1. 从 `system_config` 表查询配置键 `AUTOMATION_PLATFORM_MODULE_ID`
2. 读取 `config_value` 字段
3. 自动填充到工作流状态

---

## 五、人工审核功能

### 5.1 触发条件

数据校验发现以下问题时，工作流会暂停等待人工审核：
- ❌ 枚举值无效（不在可选范围内）
- ❌ 联动规则违反（应隐藏的字段有值、应必填的字段为空）
- ❌ 必填字段缺失

### 5.2 审核界面功能

**HumanReviewModal 组件特性**：
- ✅ 显示校验汇总信息（总数、有效数、问题数）
- ✅ 高亮显示有问题的字段
- ✅ 展示详细错误信息和修正建议
- ✅ 提供枚举值下拉选择器
- ✅ 支持快速选择常用枚举值（Tag点击）
- ✅ 内联编辑测试数据
- ✅ 三种审核操作：
  - 确认提交（approved/modified）
  - 拒绝重新生成（rejected）
  - 取消

### 5.3 审核流程

```typescript
// 提交审核结果
const handleReviewComplete = async (reviewData: any) => {
  try {
    const response = await api.post(
      `/automation/workflow/${threadId}/review`,
      {
        review_status: reviewData.review_status,  // approved/modified/rejected
        corrected_body: reviewData.corrected_body,
        feedback: reviewData.feedback
      }
    );

    if (response.data.status === 'completed') {
      message.success('自动化用例创建成功！');
    }
  } catch (error) {
    message.error('提交审核失败');
  }
};
```

---

## 六、核心优势

### 6.1 用户体验优势

| 优势 | 说明 |
|------|------|
| **极简操作** | 只需选择测试用例，点击启动 |
| **零配置** | 不需要记忆模块ID、场景ID |
| **智能匹配** | AI 自动选择最佳场景和模板 |
| **自动校验** | 三层校验确保数据质量 |
| **人工把关** | 数据有问题时支持人工修正 |
| **流程可控** | 支持暂停、恢复、重试 |

### 6.2 技术优势

| 优势 | 说明 |
|------|------|
| **状态持久化** | 使用 LangGraph Checkpointer 持久化状态 |
| **Human-in-the-Loop** | 天然支持人工介入 |
| **条件分支** | 根据校验结果动态决定流程 |
| **错误恢复** | 支持重试和降级策略 |
| **可观测性** | 每个节点输入输出可追踪 |

---

## 七、故障排查

### 7.1 常见问题

**Q1: 启动工作流时报"未找到可用场景"错误**

A: 确保：
1. 在「场景管理」中至少创建了一个场景
2. 场景状态为"启用"（`is_active=True`）
3. 场景编号 `scenario_code` 已正确填写

**Q2: 启动工作流时报"模块ID未配置"错误**

A: 在「系统配置」页面添加配置：
```
配置键: AUTOMATION_PLATFORM_MODULE_ID
配置值: 你的模块ID
```

**Q3: AI 匹配的场景不准确**

A: 检查：
1. 测试用例的业务线字段是否填写
2. 场景的业务线是否与测试用例匹配
3. 场景名称、描述是否清晰准确

**Q4: 数据校验总是失败**

A: 确认：
1. 自动化平台的字段元数据 API 是否正常
2. 枚举值和联动规则是否正确配置
3. 查看控制台日志中的详细校验错误

---

## 八、技术细节

### 8.1 文件清单

**后端文件**：
- `backend/app/services/automation_workflow_service.py` - LangGraph 工作流服务（628行）
- `backend/app/services/field_metadata_service.py` - 字段元数据服务（271行）
- `backend/app/services/body_validator.py` - 数据校验服务（318行）
- `backend/app/api/v1/endpoints/automation_workflow.py` - API 端点（211行）
- `backend/app/schemas/automation.py` - 请求/响应模型（169行）

**前端文件**：
- `frontend/src/pages/AutomationWorkflowCreate.tsx` - 主页面（简化版）
- `frontend/src/components/HumanReviewModal.tsx` - 人工审核弹窗（354行）

**测试脚本**：
- `backend/scripts/test_langgraph_workflow.py` - 端到端测试（240行）

### 8.2 依赖版本

```txt
langgraph==1.0.7
langchain==1.2.8
langchain-openai==0.3.11
```

---

## 九、相关文档

- [LangGraph 工作流详细设计](./LANGGRAPH_WORKFLOW_DESIGN.md)
- [自动化平台集成说明](./AUTOMATION_PLATFORM_INTEGRATION.md)
- [AI 选择超时优化](./AI_SELECTION_TIMEOUT_FIX.md)
- [多模型配置管理](./MULTI_MODEL_CONFIG.md)

---

## 十、更新日志

### v2.0.0 (2026-02-04) - 完全智能化

**重大改进**：
- ✅ 移除所有手动填写字段
- ✅ 只需选择测试用例即可启动
- ✅ AI 自动匹配场景
- ✅ 自动读取模块配置
- ✅ 极简化前端界面
- ✅ 操作步骤从 6 步减少到 2 步

**技术架构**：
- 新增 3 个智能节点（加载用例、匹配场景、读取配置）
- 工作流节点从 9 个增加到 12 个
- 支持完全自动化的端到端流程

### v1.0.0 (2025-11-XX) - LangGraph 初版

- LangGraph 状态机架构
- 人工审核支持
- 三层数据校验
- 9 个工作流节点
