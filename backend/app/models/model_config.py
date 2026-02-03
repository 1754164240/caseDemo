from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.db.base import Base


class ModelConfig(Base):
    """AI 模型配置表 - 支持多个模型配置"""
    __tablename__ = "model_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False, comment="模型配置名称")
    display_name = Column(String(200), nullable=False, comment="显示名称")
    description = Column(Text, comment="配置描述")

    # 模型配置信息
    api_key = Column(Text, nullable=False, comment="API Key")
    api_base = Column(String(500), nullable=False, comment="API Base URL")
    model_name = Column(Text, nullable=False, comment="模型名称列表(JSON数组格式,如[\"gpt-4\",\"gpt-3.5-turbo\"])")
    selected_model = Column(String(200), comment="当前选中使用的模型名称")

    # 可选配置
    temperature = Column(String(10), default="0.7", comment="温度参数")
    max_tokens = Column(Integer, comment="最大 token 数")

    # 模型类型和提供商
    provider = Column(String(50), comment="提供商: openai/modelscope/azure/custom")
    model_type = Column(String(50), default="chat", comment="模型类型: chat/completion")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认模型")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

