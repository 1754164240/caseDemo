"""工作流任务模型 - 记录异步工作流执行状态"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class WorkflowTask(Base):
    """工作流任务模型"""
    __tablename__ = "workflow_tasks"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String(100), unique=True, index=True, nullable=False)  # LangGraph 线程ID
    task_type = Column(String(50), default="automation_case")  # 任务类型

    # 关联信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    test_case_id = Column(Integer, ForeignKey("test_cases.id"), nullable=True, index=True)

    # 任务状态
    status = Column(String(50), default="pending", index=True)  # pending/processing/reviewing/completed/failed
    current_step = Column(String(100))  # 当前执行步骤
    progress = Column(Integer, default=0)  # 进度百分比 0-100

    # 输入参数（JSON）
    input_params = Column(JSON)

    # 执行结果（JSON）
    result_data = Column(JSON)

    # 错误信息
    error_message = Column(Text)

    # 审核相关
    need_review = Column(Boolean, default=False)  # 是否需要人工审核
    interrupt_data = Column(JSON)  # interrupt 返回的审核数据

    # 最终结果
    new_usercase_id = Column(String(100))  # 创建的自动化用例ID
    created_case = Column(JSON)  # 创建的用例信息

    # 时间记录
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))  # 开始执行时间
    completed_at = Column(DateTime(timezone=True))  # 完成时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="workflow_tasks")
    test_case = relationship("TestCase", backref="workflow_tasks")

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "task_type": self.task_type,
            "user_id": self.user_id,
            "test_case_id": self.test_case_id,
            "status": self.status,
            "current_step": self.current_step,
            "progress": self.progress,
            "input_params": self.input_params,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "need_review": self.need_review,
            "interrupt_data": self.interrupt_data,
            "new_usercase_id": self.new_usercase_id,
            "created_case": self.created_case,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
