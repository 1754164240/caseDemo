"""自动化用例相关的 Schema 定义"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Literal, Any


class CreateCaseWorkflowRequest(BaseModel):
    """启动自动化用例生成工作流请求"""

    test_case_id: int = Field(..., description="测试用例ID（用于自动获取用例信息和AI匹配场景）")
    name: Optional[str] = Field(None, description="用例名称（不传则自动生成为：测试用例标题_自动化）")
    module_id: Optional[str] = Field(None, description="模块ID（不传则从系统配置读取）")
    scene_id: Optional[str] = Field(None, description="场景ID（不传则AI自动匹配）")
    scenario_type: Optional[str] = Field("API", description="场景类型")
    description: Optional[str] = Field("", description="描述")

    class Config:
        json_schema_extra = {
            "example": {
                "test_case_id": 123,
                "scenario_type": "API",
                "description": "可选的额外描述"
            }
        }


class HumanReviewRequest(BaseModel):
    """人工审核请求"""

    review_status: Literal["approved", "modified", "rejected"] = Field(
        ...,
        description="审核状态：approved-通过，modified-修改后通过，rejected-拒绝"
    )
    corrected_body: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="修正后的测试数据"
    )
    feedback: Optional[str] = Field(None, description="反馈意见")

    class Config:
        json_schema_extra = {
            "example": {
                "review_status": "modified",
                "corrected_body": [
                    {
                        "casezf": "1",
                        "casedesc": "被保人疾病理赔",
                        "var": {
                            "CP_accidentType_1": "1",
                            "CP_accidentReason_1": "1-疾病"
                        },
                        "hoperesult": "成功结案",
                        "iscaserun": False,
                        "caseBodySN": 1
                    }
                ],
                "feedback": "修正了出险类型和出险原因字段"
            }
        }


class WorkflowStateResponse(BaseModel):
    """工作流状态响应"""

    thread_id: str = Field(..., description="工作流线程ID")
    status: str = Field(..., description="当前状态")
    current_step: str = Field(..., description="当前步骤")
    need_human_review: bool = Field(..., description="是否需要人工审核")
    state: Dict[str, Any] = Field(..., description="完整状态数据")

    class Config:
        json_schema_extra = {
            "example": {
                "thread_id": "workflow_1_a3f2c9d1",
                "status": "reviewing",
                "current_step": "awaiting_human_review",
                "need_human_review": True,
                "state": {
                    "name": "理赔测试用例_001",
                    "generated_body": [],
                    "validation_result": {
                        "total": 3,
                        "valid_count": 2,
                        "invalid_count": 1,
                        "total_errors": 2
                    }
                }
            }
        }


class WorkflowResultResponse(BaseModel):
    """工作流执行结果响应"""

    thread_id: str = Field(..., description="工作流线程ID")
    status: str = Field(..., description="最终状态")
    current_step: str = Field(..., description="当前步骤")
    created_case: Optional[Dict[str, Any]] = Field(None, description="创建的用例信息")
    new_usercase_id: Optional[str] = Field(None, description="新创建的用例ID")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        json_schema_extra = {
            "example": {
                "thread_id": "workflow_1_a3f2c9d1",
                "status": "completed",
                "current_step": "case_created",
                "created_case": {
                    "usercaseId": "UC_12345",
                    "name": "理赔测试用例_001"
                },
                "new_usercase_id": "UC_12345",
                "error": None
            }
        }


class ValidationError(BaseModel):
    """校验错误"""

    field: str = Field(..., description="字段名")
    fieldName: Optional[str] = Field(None, description="字段中文名")
    value: Optional[Any] = Field(None, description="当前值")
    type: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    suggestion: Optional[str] = Field(None, description="修正建议")
    validValues: Optional[List[str]] = Field(None, description="有效值列表")


class ValidationResult(BaseModel):
    """校验结果"""

    valid: bool = Field(..., description="是否有效")
    errors: List[ValidationError] = Field(default_factory=list, description="错误列表")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="警告列表")
    suggestions: List[Dict[str, Any]] = Field(default_factory=list, description="建议列表")
