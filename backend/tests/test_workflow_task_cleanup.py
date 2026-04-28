import unittest

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db.base import Base, import_models
from app.models.requirement import Requirement, FileType
from app.models.test_case import TestCase
from app.models.test_point import TestPoint
from app.models.user import User
from app.models.workflow_task import WorkflowTask
from app.services.workflow_task_cleanup import detach_workflow_tasks_from_test_cases

import_models()


class WorkflowTaskCleanupTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")

        @event.listens_for(self.engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_detach_workflow_tasks_before_deleting_test_cases(self):
        db = self.SessionLocal()
        try:
            user = User(
                email="tester@example.com",
                username="tester",
                hashed_password="password",
            )
            db.add(user)
            db.flush()

            requirement = Requirement(
                title="需求",
                file_name="demo.txt",
                file_path="demo.txt",
                file_type=FileType.TXT,
                file_size=1,
                user_id=user.id,
            )
            db.add(requirement)
            db.flush()

            test_point = TestPoint(
                requirement_id=requirement.id,
                code="TP-001",
                title="测试点",
            )
            db.add(test_point)
            db.flush()

            test_case = TestCase(
                test_point_id=test_point.id,
                code="TP-001-1",
                title="测试用例",
            )
            db.add(test_case)
            db.flush()

            workflow_task = WorkflowTask(
                thread_id="thread-1",
                user_id=user.id,
                test_case_id=test_case.id,
            )
            db.add(workflow_task)
            db.commit()

            detach_workflow_tasks_from_test_cases(db, [test_case.id])
            db.delete(test_case)
            db.commit()

            saved_task = db.query(WorkflowTask).filter_by(id=workflow_task.id).one()
            self.assertIsNone(saved_task.test_case_id)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
