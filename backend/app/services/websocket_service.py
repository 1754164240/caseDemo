from typing import Dict, Set
from fastapi import WebSocket
import json


class ConnectionManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # 存储活动连接：user_id -> Set[WebSocket]
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """接受新连接"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """断开连接"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: int):
        """发送个人消息"""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message, ensure_ascii=False))
                except:
                    disconnected.add(connection)
            
            # 清理断开的连接
            for conn in disconnected:
                self.active_connections[user_id].discard(conn)
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        for user_connections in self.active_connections.values():
            for connection in user_connections:
                try:
                    await connection.send_text(json.dumps(message, ensure_ascii=False))
                except:
                    pass
    
    async def notify_test_point_generated(self, user_id: int, requirement_id: int, test_points_count: int):
        """通知测试点生成完成"""
        message = {
            "type": "test_points_generated",
            "requirement_id": requirement_id,
            "count": test_points_count,
            "message": f"测试点生成完成，共 {test_points_count} 个"
        }
        await self.send_personal_message(message, user_id)
    
    async def notify_test_point_failed(self, user_id: int, requirement_id: int, error_message: str):
        """Notify client that test point regeneration failed"""
        message = {
            "type": "test_points_failed",
            "requirement_id": requirement_id,
            "message": error_message,
        }
        await self.send_personal_message(message, user_id)
    
    async def notify_test_case_generated(self, user_id: int, test_point_id: int, test_cases_count: int):
        """通知测试用例生成完成"""
        message = {
            "type": "test_cases_generated",
            "test_point_id": test_point_id,
            "count": test_cases_count,
            "message": f"测试用例生成完成，共 {test_cases_count} 个"
        }
        await self.send_personal_message(message, user_id)
    
    async def notify_progress(self, user_id: int, task_type: str, progress: int, message: str):
        """通知进度更新"""
        notification = {
            "type": "progress",
            "task_type": task_type,
            "progress": progress,
            "message": message
        }
        await self.send_personal_message(notification, user_id)

    async def notify_workflow_progress(self, user_id: int, thread_id: str, step_name: str, step_index: int, total_steps: int, status: str, message: str):
        """通知工作流进度更新"""
        notification = {
            "type": "workflow_progress",
            "thread_id": thread_id,
            "step_name": step_name,
            "step_index": step_index,
            "total_steps": total_steps,
            "status": status,  # running, completed, failed
            "message": message,
            "progress": int((step_index / total_steps) * 100) if total_steps > 0 else 0
        }
        await self.send_personal_message(notification, user_id)


manager = ConnectionManager()


# 辅助函数：发送消息给指定用户
async def send_message_to_user(user_id: int, message_type: str, data: dict):
    """
    发送消息给指定用户

    Args:
        user_id: 用户ID
        message_type: 消息类型
        data: 消息数据
    """
    message = {
        "type": message_type,
        "data": data
    }
    await manager.send_personal_message(message, user_id)
