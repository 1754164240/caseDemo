from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.requirement import Requirement
from app.models.test_point import TestPoint
from app.models.test_case import TestCase
from app.core.config import settings

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取首页统计数据"""
    
    # 需求数量
    requirements_count = db.query(func.count(Requirement.id)).filter(
        Requirement.user_id == current_user.id
    ).scalar()
    
    # 测试点数量
    test_points_count = db.query(func.count(TestPoint.id)).join(Requirement).filter(
        Requirement.user_id == current_user.id
    ).scalar()
    
    # 测试用例数量
    test_cases_count = db.query(func.count(TestCase.id)).join(TestPoint).join(Requirement).filter(
        Requirement.user_id == current_user.id
    ).scalar()
    
    # 当前使用模型
    current_model = settings.MODEL_NAME
    
    # 最近的需求
    recent_requirements = db.query(Requirement).filter(
        Requirement.user_id == current_user.id
    ).order_by(Requirement.created_at.desc()).limit(5).all()

    # 最近的测试用例
    recent_test_cases = db.query(TestCase).join(TestPoint).join(Requirement).filter(
        Requirement.user_id == current_user.id
    ).order_by(TestCase.created_at.desc()).limit(10).all()

    return {
        "requirements_count": requirements_count,
        "test_points_count": test_points_count,
        "test_cases_count": test_cases_count,
        "current_model": current_model,
        "recent_requirements": [
            {
                "id": req.id,
                "title": req.title,
                "status": req.status.value,
                "created_at": req.created_at.isoformat()
            }
            for req in recent_requirements
        ],
        "recent_test_cases": [
            {
                "id": tc.id,
                "title": tc.title,
                "priority": tc.priority,
                "test_type": tc.test_type,
                "test_point_title": tc.test_point.title if tc.test_point else None,
                "requirement_title": tc.test_point.requirement.title if tc.test_point and tc.test_point.requirement else None,
                "created_at": tc.created_at.isoformat()
            }
            for tc in recent_test_cases
        ]
    }

