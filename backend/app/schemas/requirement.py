from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.requirement import FileType, RequirementStatus


class RequirementBase(BaseModel):
    title: str
    description: Optional[str] = None


class RequirementCreate(RequirementBase):
    pass


class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[RequirementStatus] = None


class RequirementInDB(RequirementBase):
    id: int
    file_name: str
    file_path: str
    file_type: FileType
    file_size: Optional[int] = None
    status: RequirementStatus
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Requirement(RequirementInDB):
    pass


class RequirementWithStats(Requirement):
    test_points_count: int = 0
    test_cases_count: int = 0

