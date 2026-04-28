import unittest
from unittest.mock import Mock, patch

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.endpoints import requirements as requirements_module
from app.db.base import Base, import_models
from app.models.requirement import FileType, Requirement
from app.models.test_point_history import TestPointHistory
from app.models.test_point import TestPoint
from app.models.user import User

import_models()


class FakeAIService:
    def __init__(self):
        self.called = False

    def extract_test_points(self, requirement_text, allow_fallback=True):
        self.called = True
        return [
            {
                "title": "数据库模型生成的测试点",
                "description": "来自数据库模型配置",
                "category": "功能",
                "priority": "high",
                "business_line": "contract",
            }
        ]


class RequirementAIConfigTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @event.listens_for(self.engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        db = self.SessionLocal()
        try:
            user = User(
                email="tester@example.com",
                username="tester",
                hashed_password="password",
            )
            db.add(user)
            db.flush()
            self.user_id = user.id

            requirement = Requirement(
                title="需求",
                file_name="demo.txt",
                file_path="demo.txt",
                file_type=FileType.TXT,
                file_size=1,
                user_id=user.id,
            )
            db.add(requirement)
            db.commit()
            self.requirement_id = requirement.id
        finally:
            db.close()

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def test_upload_processing_uses_database_model_config_when_env_key_is_empty(self):
        fake_ai_service = FakeAIService()

        with (
            patch.object(requirements_module, "SessionLocal", self.SessionLocal),
            patch.object(requirements_module.settings, "OPENAI_API_KEY", ""),
            patch.object(requirements_module.DocumentParser, "parse", return_value="有效内容" * 120),
            patch.object(
                requirements_module.DocumentParser,
                "evaluate_quality",
                return_value={"meaningful_chars": 480, "non_empty_ratio": 1.0},
            ),
            patch.object(
                requirements_module.document_embedding_service,
                "split_text",
                return_value=["片段一", "片段二"],
            ),
            patch.object(
                requirements_module.document_embedding_service,
                "process_and_store",
                return_value=0,
            ),
            patch.object(
                requirements_module.document_embedding_service,
                "build_ai_context",
                return_value="构建后的上下文",
            ),
            patch.object(requirements_module, "get_ai_service", return_value=fake_ai_service),
            patch.object(requirements_module, "allocate_requirement_version", return_value="v1"),
            patch.object(requirements_module, "record_history_entry"),
            patch.object(requirements_module.manager, "notify_test_point_generated", new=Mock(return_value=None)),
        ):
            requirements_module.process_requirement_background(
                self.requirement_id,
                self.user_id,
                loop=None,
            )

        db = self.SessionLocal()
        try:
            saved_points = db.query(TestPoint).all()
            self.assertTrue(fake_ai_service.called)
            self.assertEqual(1, len(saved_points))
            self.assertEqual("数据库模型生成的测试点", saved_points[0].title)
        finally:
            db.close()

    def test_delete_requirement_removes_test_point_histories_first(self):
        db = self.SessionLocal()
        try:
            user = db.query(User).filter(User.id == self.user_id).one()
            test_point = TestPoint(
                requirement_id=self.requirement_id,
                code="TP-001",
                title="测试点",
            )
            db.add(test_point)
            db.flush()
            db.add(
                TestPointHistory(
                    test_point_id=test_point.id,
                    requirement_id=self.requirement_id,
                    version="v1",
                    code=test_point.code,
                    title=test_point.title,
                    status="completed",
                )
            )
            db.commit()

            with patch.object(requirements_module, "resolve_file_path") as mock_resolve:
                mock_resolve.return_value.exists.return_value = False
                response = requirements_module.delete_requirement(
                    self.requirement_id,
                    db=db,
                    current_user=user,
                )

            self.assertEqual({"message": "Requirement deleted successfully"}, response)
            self.assertEqual(0, db.query(TestPointHistory).count())
            self.assertEqual(0, db.query(TestPoint).count())
            self.assertEqual(0, db.query(Requirement).count())
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
