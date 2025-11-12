from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all models here for Alembic
# Note: Imports are at the end to avoid circular import issues
def import_models():
    """Import all models to ensure they are registered with SQLAlchemy"""
    from app.models.user import User
    from app.models.requirement import Requirement
    from app.models.test_point import TestPoint
    from app.models.test_case import TestCase
    from app.models.system_config import SystemConfig
    from app.models.knowledge_base import KnowledgeDocument, QARecord
    from app.models.model_config import ModelConfig
    return User, Requirement, TestPoint, TestCase, SystemConfig, KnowledgeDocument, QARecord, ModelConfig

