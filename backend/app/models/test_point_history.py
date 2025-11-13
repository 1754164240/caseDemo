from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.db.base import Base


class TestPointHistory(Base):
    __tablename__ = "test_point_histories"

    id = Column(Integer, primary_key=True, index=True)
    test_point_id = Column(Integer, ForeignKey("test_points.id"), nullable=False, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=False, index=True)
    version = Column(String(50), nullable=False, index=True)
    code = Column(String(20))
    title = Column(String(200))
    description = Column(Text)
    category = Column(String(100))
    priority = Column(String(20))
    business_line = Column(String(50))
    prompt_summary = Column(Text)
    status = Column(String(20), default="pending")
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
