from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SystemConfigBase(BaseModel):
    config_key: str
    config_value: str
    description: Optional[str] = None


class SystemConfigCreate(SystemConfigBase):
    pass


class SystemConfigUpdate(BaseModel):
    config_value: str
    description: Optional[str] = None


class SystemConfigInDB(SystemConfigBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SystemConfig(SystemConfigInDB):
    pass


# 特定配置的 Schema
class MilvusConfigUpdate(BaseModel):
    host: str
    port: int


class ModelConfigUpdate(BaseModel):
    api_key: str
    api_base: str
    model_name: str

