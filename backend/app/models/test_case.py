from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    test_point_id = Column(Integer, ForeignKey("test_points.id"), nullable=False)
    code = Column(String(30), unique=True, index=True)  # 测试用例编号，如 TP-001-1
    title = Column(String(200), nullable=False)
    description = Column(Text)
    preconditions = Column(Text)  # 前置条件
    test_steps = Column(JSON)  # 测试步骤 [{"step": 1, "action": "...", "expected": "..."}]
    expected_result = Column(Text)  # 预期结果
    priority = Column(String(20))  # high, medium, low
    test_type = Column(String(50))  # functional, performance, security, etc.

    # 审批相关字段
    approval_status = Column(String(20), default='pending')  # pending, approved, rejected
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime(timezone=True))
    approval_comment = Column(Text)  # 审批意见

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    test_point = relationship("TestPoint", back_populates="test_cases")
    approver = relationship("User", foreign_keys=[approved_by])

