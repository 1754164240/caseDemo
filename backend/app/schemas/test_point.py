from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class TestPointBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = "medium"
    business_line: Optional[str] = None  # contract(契约)/preservation(保全)/claim(理赔)


class TestPointCreate(TestPointBase):
    requirement_id: int


class TestPointUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    business_line: Optional[str] = None
    is_approved: Optional[bool] = None
    user_feedback: Optional[str] = None


class TestPointApproval(BaseModel):
    """审批操作的请求模型"""
    approval_status: str  # approved 或 rejected
    approval_comment: Optional[str] = None


class TestPointOptimizeRequest(BaseModel):
    requirement_id: int
    selected_ids: List[int] = Field(default_factory=list)
    mode: str = "single"  # single / batch
    per_point_prompts: Dict[int, str] = Field(default_factory=dict)
    batch_prompt: Optional[str] = None
    business_info: Optional[str] = None
    version_note: Optional[str] = None


class TestPointBulkUpdateItem(BaseModel):
    id: int
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    business_line: Optional[str] = None
    user_feedback: Optional[str] = None
    approval_status: Optional[str] = None


class TestPointBulkUpdateRequest(BaseModel):
    requirement_id: int
    updates: List[TestPointBulkUpdateItem]


class TestPointInDB(TestPointBase):
    id: int
    requirement_id: int
    code: str  # 测试点编号
    is_approved: bool
    user_feedback: Optional[str] = None

    # 审批相关字段
    approval_status: str = 'pending'
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approval_comment: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestPoint(TestPointInDB):
    pass


class TestPointWithCases(TestPoint):
    test_cases_count: int = 0


class TestPointHistoryEntry(BaseModel):
    id: int
    version: str
    title: Optional[str] = None
    description: Optional[str] = None
    prompt_summary: Optional[str] = None
    status: str
    operator_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

