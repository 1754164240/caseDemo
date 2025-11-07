from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class TestPoint(Base):
    __tablename__ = "test_points"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=False)
    code = Column(String(20), unique=True, index=True)  # 测试点编号，如 TP-001
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    priority = Column(String(20))  # high, medium, low
    is_approved = Column(Boolean, default=False)  # 保留用于兼容性
    user_feedback = Column(Text)  # 用户修改意见

    # 审批相关字段
    approval_status = Column(String(20), default='pending')  # pending, approved, rejected
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    approval_comment = Column(Text)  # 审批意见

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    requirement = relationship("Requirement", back_populates="test_points")
    test_cases = relationship("TestCase", back_populates="test_point", cascade="all, delete-orphan")
    approver = relationship("User", foreign_keys=[approved_by])

