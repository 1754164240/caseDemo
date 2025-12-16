from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ScenarioBase(BaseModel):
    """场景基础模型"""
    scenario_code: str = Field(..., description="场景ID/编号，如 SC-001")
    name: str = Field(..., description="场景名称")
    description: Optional[str] = Field(None, description="场景描述")
    business_line: Optional[str] = Field(None, description="业务线：contract(契约)/preservation(保全)/claim(理赔)")
    channel: Optional[str] = Field(None, description="渠道：线上/线下/移动端等")
    module: Optional[str] = Field(None, description="所属模块")
    is_active: bool = Field(True, description="是否启用")


class ScenarioCreate(ScenarioBase):
    """创建场景请求模型"""
    pass


class ScenarioUpdate(BaseModel):
    """更新场景请求模型"""
    scenario_code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    business_line: Optional[str] = None
    channel: Optional[str] = None
    module: Optional[str] = None
    is_active: Optional[bool] = None


class ScenarioInDB(ScenarioBase):
    """数据库中的场景模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Scenario(ScenarioInDB):
    """场景响应模型"""
    pass

