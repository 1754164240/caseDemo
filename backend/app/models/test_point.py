from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class TestPoint(Base):
    __tablename__ = "test_points"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    priority = Column(String(20))  # high, medium, low
    is_approved = Column(Boolean, default=False)
    user_feedback = Column(Text)  # 用户修改意见
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    requirement = relationship("Requirement", back_populates="test_points")
    test_cases = relationship("TestCase", back_populates="test_point", cascade="all, delete-orphan")

