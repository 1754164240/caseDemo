from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from app.db.base import Base


class Scenario(Base):
    """场景模型"""
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    scenario_code = Column(String(50), unique=True, index=True, nullable=False)  # 场景ID/编号，如 SC-001
    name = Column(String(200), nullable=False, index=True)  # 场景名称
    description = Column(Text)  # 描述
    business_line = Column(String(50), index=True)  # 业务线：contract(契约)/preservation(保全)/claim(理赔)
    channel = Column(String(100))  # 渠道：线上/线下/移动端等
    module = Column(String(100), index=True)  # 模块
    is_active = Column(Boolean, default=True)  # 是否启用
    
    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

