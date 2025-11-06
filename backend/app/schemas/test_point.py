from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TestPointBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = "medium"


class TestPointCreate(TestPointBase):
    requirement_id: int


class TestPointUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    is_approved: Optional[bool] = None
    user_feedback: Optional[str] = None


class TestPointInDB(TestPointBase):
    id: int
    requirement_id: int
    is_approved: bool
    user_feedback: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestPoint(TestPointInDB):
    pass


class TestPointWithCases(TestPoint):
    test_cases_count: int = 0

