from pydantic import BaseModel
from typing import Optional, List
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

