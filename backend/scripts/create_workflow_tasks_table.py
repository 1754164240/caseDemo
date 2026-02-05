"""创建 workflow_tasks 表的迁移脚本"""

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.db.base import Base

# 导入所有模型以确保外键依赖正确
from app.models.user import User
from app.models.test_case import TestCase
from app.models.workflow_task import WorkflowTask

def create_workflow_tasks_table():
    """创建 workflow_tasks 表（自动处理依赖）"""
    try:
        engine = create_engine(settings.DATABASE_URL)

        print("[INFO] 开始创建 workflow_tasks 表...")
        print("[INFO] 检查依赖表: users, test_cases")

        # 创建所有表（如果已存在则跳过）
        # SQLAlchemy 会自动处理表的依赖顺序
        Base.metadata.create_all(bind=engine)

        print("[SUCCESS] workflow_tasks 表创建成功!")
        print("[INFO] 相关表已确保存在: users, test_cases, workflow_tasks")

    except Exception as e:
        print(f"[ERROR] 创建表失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_workflow_tasks_table()
