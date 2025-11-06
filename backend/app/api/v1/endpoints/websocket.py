from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from app.services.websocket_service import manager
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.websocket("/notifications")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """WebSocket 连接端点"""
    # 这里简化了认证，实际应该验证 token
    # 为了演示，我们假设 token 包含 user_id
    try:
        user_id = int(token)  # 实际应该解析 JWT token
    except:
        await websocket.close(code=1008)
        return
    
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # 接收客户端消息（保持连接）
            data = await websocket.receive_text()
            # 可以处理客户端发送的消息
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

