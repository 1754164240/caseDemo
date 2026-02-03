from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union
from datetime import datetime
import json


class ModelConfigBase(BaseModel):
    """模型配置基础 Schema"""
    name: str = Field(..., description="模型配置名称(唯一标识)")
    display_name: str = Field(..., description="显示名称")
    description: Optional[str] = Field(None, description="配置描述")
    api_key: str = Field(..., description="API Key")
    api_base: str = Field(..., description="API Base URL")
    model_name: Union[str, List[str]] = Field(..., description="模型名称(单个字符串或字符串数组)")
    selected_model: Optional[str] = Field(None, description="当前选中使用的模型名称")
    temperature: Optional[str] = Field("1.0", description="温度参数")
    max_tokens: Optional[int] = Field(None, description="最大 token 数")
    provider: Optional[str] = Field(None, description="提供商: openai/modelscope/azure/custom")
    model_type: Optional[str] = Field("chat", description="模型类型: chat/completion")
    is_active: Optional[bool] = Field(True, description="是否启用")

    @field_validator('model_name')
    @classmethod
    def validate_model_name(cls, v):
        """验证并标准化模型名称"""
        if isinstance(v, str):
            # 单个模型名称，转换为列表
            return [v.strip()] if v.strip() else []
        elif isinstance(v, list):
            # 过滤空字符串
            return [name.strip() for name in v if name and name.strip()]
        else:
            raise ValueError("model_name必须是字符串或字符串数组")


class ModelConfigCreate(ModelConfigBase):
    """创建模型配置"""
    pass


class ModelConfigUpdate(BaseModel):
    """更新模型配置"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model_name: Optional[Union[str, List[str]]] = None
    selected_model: Optional[str] = None
    temperature: Optional[str] = None
    max_tokens: Optional[int] = None
    provider: Optional[str] = None
    model_type: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('model_name')
    @classmethod
    def validate_model_name(cls, v):
        """验证并标准化模型名称"""
        if v is None:
            return None
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        elif isinstance(v, list):
            return [name.strip() for name in v if name and name.strip()]
        else:
            raise ValueError("model_name必须是字符串或字符串数组")


class ModelConfigInDB(BaseModel):
    """数据库中的模型配置"""
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    api_key: str
    api_base: str
    model_name: Union[str, List[str]]  # 从数据库读取时可能是JSON字符串或列表
    selected_model: Optional[str] = None
    temperature: Optional[str] = None
    max_tokens: Optional[int] = None
    provider: Optional[str] = None
    model_type: Optional[str] = None
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ModelConfig(ModelConfigInDB):
    """返回给前端的模型配置(隐藏完整 API Key)"""
    api_key_masked: Optional[str] = Field(None, description="脱敏后的 API Key")

    @classmethod
    def from_db(cls, db_model):
        """从数据库模型创建,并脱敏 API Key"""
        # 解析模型名称（可能是JSON字符串）
        model_name = db_model.model_name
        if isinstance(model_name, str):
            try:
                # 尝试解析为JSON数组
                model_name = json.loads(model_name)
            except (json.JSONDecodeError, ValueError):
                # 如果不是JSON,当作单个模型名称
                model_name = [model_name] if model_name else []

        data = {
            "id": db_model.id,
            "name": db_model.name,
            "display_name": db_model.display_name,
            "description": db_model.description,
            "api_key": db_model.api_key,
            "api_base": db_model.api_base,
            "model_name": model_name,
            "selected_model": db_model.selected_model,
            "temperature": db_model.temperature,
            "max_tokens": db_model.max_tokens,
            "provider": db_model.provider,
            "model_type": db_model.model_type,
            "is_active": db_model.is_active,
            "is_default": db_model.is_default,
            "created_at": db_model.created_at,
            "updated_at": db_model.updated_at,
        }

        # 脱敏 API Key
        api_key = db_model.api_key
        if api_key and len(api_key) > 8:
            data["api_key_masked"] = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
        else:
            data["api_key_masked"] = api_key

        return cls(**data)


class ModelConfigResponse(BaseModel):
    """模型配置响应(用于列表)"""
    id: int
    name: str
    display_name: str
    description: Optional[str] = None
    api_key_masked: str = Field(..., description="脱敏后的 API Key")
    api_base: str
    model_name: Union[str, List[str]]
    selected_model: Optional[str] = None
    temperature: Optional[str] = None
    max_tokens: Optional[int] = None
    provider: Optional[str] = None
    model_type: Optional[str] = None
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SetDefaultModelRequest(BaseModel):
    """设置默认模型请求"""
    model_id: int = Field(..., description="要设置为默认的模型配置 ID")

