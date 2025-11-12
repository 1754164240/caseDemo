from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, requirements, test_points, test_cases, dashboard, websocket, system_config, knowledge_base, model_config

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(requirements.router, prefix="/requirements", tags=["需求管理"])
api_router.include_router(test_points.router, prefix="/test-points", tags=["测试点管理"])
api_router.include_router(test_cases.router, prefix="/test-cases", tags=["测试用例管理"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["首页"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
api_router.include_router(system_config.router, prefix="/system-config", tags=["系统配置"])
api_router.include_router(model_config.router, prefix="/model-configs", tags=["模型配置"])
api_router.include_router(knowledge_base.router, prefix="/knowledge-base", tags=["知识库"])

