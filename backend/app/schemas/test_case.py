from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class TestStep(BaseModel):
    step: int
    action: str
    expected: str


class TestCaseBase(BaseModel):
    title: str
    description: Optional[str] = None
    preconditions: Optional[str] = None
    test_steps: Optional[List[Dict[str, Any]]] = None
    expected_result: Optional[str] = None
    priority: Optional[str] = "medium"
    test_type: Optional[str] = "functional"


class TestCaseCreate(TestCaseBase):
    test_point_id: int


class TestCaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    preconditions: Optional[str] = None
    test_steps: Optional[List[Dict[str, Any]]] = None
    expected_result: Optional[str] = None
    priority: Optional[str] = None
    test_type: Optional[str] = None


class TestCaseApproval(BaseModel):
    """审批操作的请求模型"""
    approval_status: str  # approved 或 rejected
    approval_comment: Optional[str] = None


class TestCaseInDB(TestCaseBase):
    id: int
    test_point_id: int
    code: str  # 测试用例编号

    # 审批相关字段
    approval_status: str = 'pending'
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    approval_comment: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestCase(TestCaseInDB):
    pass

