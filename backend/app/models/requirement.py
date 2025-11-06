from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class FileType(str, enum.Enum):
    DOCX = "docx"
    PDF = "pdf"
    TXT = "txt"
    XLS = "xls"
    XLSX = "xlsx"


class RequirementStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    file_size = Column(Integer)
    status = Column(Enum(RequirementStatus), default=RequirementStatus.UPLOADED)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    test_points = relationship("TestPoint", back_populates="requirement", cascade="all, delete-orphan")

