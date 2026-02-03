from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import json

from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.requirement import Requirement
from app.models.test_point import TestPoint
from app.models.test_case import TestCase
from app.models.model_config import ModelConfig
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

    # 当前使用模型 - 从模型配置表获取默认模型
    current_model = settings.MODEL_NAME  # 默认值
    model_config_info = None

    try:
        default_model_config = db.query(ModelConfig).filter(
            ModelConfig.is_default == True,
            ModelConfig.is_active == True
        ).first()

        if default_model_config:
            # 解析模型名称列表
            model_names = default_model_config.model_name
            if isinstance(model_names, str):
                try:
                    model_names = json.loads(model_names)
                except (json.JSONDecodeError, ValueError):
                    model_names = [model_names] if model_names else []

            # 确保 model_names 是列表
            if not isinstance(model_names, list):
                model_names = [model_names] if model_names else []

            # 当前使用的模型：优先使用 selected_model，否则使用第一个模型
            selected = default_model_config.selected_model
            if selected and selected.strip():  # 确保 selected_model 不为空
                current_model = selected.strip()
            elif model_names:
                current_model = model_names[0]
            else:
                current_model = settings.MODEL_NAME

            # 模型配置详细信息
            model_config_info = {
                "config_name": default_model_config.display_name,
                "current_model": current_model,
                "all_models": model_names,
                "provider": default_model_config.provider,
                "api_base": default_model_config.api_base
            }
    except Exception as e:
        # 如果查询失败，使用环境变量中的配置
        print(f"[WARNING] 获取默认模型配置失败: {e}")
        import traceback
        traceback.print_exc()
        model_config_info = {
            "config_name": "环境变量配置",
            "current_model": current_model,
            "all_models": [current_model],
            "provider": "env",
            "api_base": settings.OPENAI_API_BASE
        }

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
        "model_config": model_config_info,  # 新增：完整模型配置信息
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

