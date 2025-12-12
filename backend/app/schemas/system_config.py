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
    uri: str
    user: str
    password: str
    token: str
    db_name: str
    collection_name: str


class ModelConfigUpdate(BaseModel):
    api_key: str
    api_base: str
    model_name: str


class EmbeddingConfigUpdate(BaseModel):
    """Embedding 模型配置"""
    embedding_model: str
    embedding_api_key: str
    embedding_api_base: str


class AutomationPlatformConfigUpdate(BaseModel):
    """自动化测试平台配置"""
    api_base: str


class PromptConfigUpdate(BaseModel):
    test_point_prompt: str
    test_case_prompt: str
    contract_test_case_prompt: str  # 契约业务线测试用例 Prompt
    preservation_test_case_prompt: str  # 保全业务线测试用例 Prompt
    claim_test_case_prompt: str  # 理赔业务线测试用例 Prompt
