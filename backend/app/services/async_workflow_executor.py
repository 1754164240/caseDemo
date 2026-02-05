"""异步工作流执行器 - 后台执行工作流并更新任务状态"""

import asyncio
import traceback
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.workflow_task import WorkflowTask
from app.services.automation_workflow_service import AutomationWorkflowService
from app.services.websocket_service import send_message_to_user


def make_json_serializable(obj):
    """
    将对象转换为 JSON 可序列化的格式
    处理 LangGraph Interrupt 对象等特殊类型
    """
    if obj is None:
        return None

    # 处理字典
    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            # 跳过不可序列化的对象（如 Interrupt）
            if hasattr(value, '__class__') and 'Interrupt' in value.__class__.__name__:
                continue
            result[key] = make_json_serializable(value)
        return result

    # 处理列表
    if isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]

    # 基本类型直接返回
    if isinstance(obj, (str, int, float, bool)):
        return obj

    # 其他对象尝试转换为字符串
    try:
        return str(obj)
    except:
        return None


def update_task_status(
    db: Session,
    thread_id: str,
    status: str = None,
    current_step: str = None,
    progress: int = None,
    error_message: str = None,
    result_data: Dict = None,
    need_review: bool = None,
    interrupt_data: Dict = None,
    new_usercase_id: str = None,
    created_case: Dict = None
):
    """更新工作流任务状态"""
    try:
        task = db.query(WorkflowTask).filter(WorkflowTask.thread_id == thread_id).first()
        if not task:
            return

        if status:
            task.status = status
        if current_step:
            task.current_step = current_step
        if progress is not None:
            task.progress = progress
        if error_message:
            task.error_message = error_message
        if result_data:
            # 清理不可序列化的对象
            task.result_data = make_json_serializable(result_data)
        if need_review is not None:
            task.need_review = need_review
        if interrupt_data:
            # 清理不可序列化的对象
            serialized = make_json_serializable(interrupt_data)
            print(f"[DEBUG] 序列化前 interrupt_data 键: {interrupt_data.keys() if isinstance(interrupt_data, dict) else 'N/A'}")
            print(f"[DEBUG] 序列化后 interrupt_data 键: {serialized.keys() if isinstance(serialized, dict) else 'N/A'}")
            if isinstance(serialized, dict):
                gen_body_ser = serialized.get('generated_body', [])
                print(f"[DEBUG] 序列化后 generated_body 类型: {type(gen_body_ser)}")
                print(f"[DEBUG] 序列化后 generated_body 数量: {len(gen_body_ser) if isinstance(gen_body_ser, list) else 'N/A'}")
                if isinstance(gen_body_ser, list) and len(gen_body_ser) > 0:
                    print(f"[DEBUG] 序列化后 generated_body[0]: {gen_body_ser[0]}")
            task.interrupt_data = serialized
        if new_usercase_id:
            task.new_usercase_id = new_usercase_id
        if created_case:
            task.created_case = make_json_serializable(created_case)

        # 更新时间戳
        if status == "processing" and not task.started_at:
            task.started_at = datetime.now()
        if status in ["completed", "failed"]:
            task.completed_at = datetime.now()

        db.commit()
        db.refresh(task)
        return task
    except Exception as e:
        print(f"[ERROR] 更新任务状态失败: {e}")
        db.rollback()
        return None


async def execute_workflow_async(
    thread_id: str,
    initial_state: Dict[str, Any],
    user_id: int,
    db: Session
):
    """
    异步执行工作流

    Args:
        thread_id: 线程ID
        initial_state: 初始状态
        user_id: 用户ID
        db: 数据库会话
    """
    print(f"[异步工作流] 开始执行工作流 {thread_id}")

    try:
        # 更新状态为处理中
        update_task_status(
            db, thread_id,
            status="processing",
            current_step="initializing",
            progress=5
        )

        # 推送WebSocket消息
        await send_message_to_user(
            user_id=user_id,
            message_type="workflow_started",
            data={
                "thread_id": thread_id,
                "status": "processing",
                "message": "工作流已启动，正在执行..."
            }
        )

        # 创建工作流服务
        workflow_svc = AutomationWorkflowService(db)

        # 执行工作流（会在 human_review 节点暂停）
        result_state = workflow_svc.start_workflow(initial_state, thread_id)

        status = result_state.get("status", "unknown")
        current_step = result_state.get("current_step", "unknown")

        print(f"[异步工作流] 工作流执行到: {current_step}, 状态: {status}")

        # 根据状态更新任务
        if status == "reviewing":
            # 需要人工审核
            interrupt_data_raw = result_state.get("interrupt_data")
            print(f"[异步工作流] interrupt_data 类型: {type(interrupt_data_raw)}")
            print(f"[异步工作流] interrupt_data 键: {interrupt_data_raw.keys() if isinstance(interrupt_data_raw, dict) else 'N/A'}")

            # 检查关键字段
            if isinstance(interrupt_data_raw, dict):
                gen_body = interrupt_data_raw.get('generated_body', [])
                print(f"[异步工作流] generated_body 类型: {type(gen_body)}")
                print(f"[异步工作流] generated_body 数量: {len(gen_body) if isinstance(gen_body, list) else 'N/A'}")
                if isinstance(gen_body, list) and len(gen_body) > 0:
                    print(f"[异步工作流] generated_body[0] 类型: {type(gen_body[0])}")
                    print(f"[异步工作流] generated_body[0] 键: {gen_body[0].keys() if isinstance(gen_body[0], dict) else 'N/A'}")
                print(f"[异步工作流] field_metadata 存在: {bool(interrupt_data_raw.get('field_metadata'))}")

            update_task_status(
                db, thread_id,
                status="reviewing",
                current_step=current_step,
                progress=80,
                need_review=True,
                interrupt_data=interrupt_data_raw,
                result_data=result_state
            )

            # 推送审核通知
            await send_message_to_user(
                user_id=user_id,
                message_type="workflow_need_review",
                data={
                    "thread_id": thread_id,
                    "status": "reviewing",
                    "message": "AI已生成测试数据，请进行人工审核",
                    "interrupt_data": result_state.get("interrupt_data"),
                    "validation_result": result_state.get("validation_result"),
                    "generated_body": result_state.get("generated_body", [])
                }
            )

        elif status == "failed":
            # 执行失败
            error_msg = result_state.get("error", "工作流执行失败")
            update_task_status(
                db, thread_id,
                status="failed",
                current_step=current_step,
                progress=0,
                error_message=error_msg,
                result_data=result_state
            )

            # 推送失败通知
            await send_message_to_user(
                user_id=user_id,
                message_type="workflow_failed",
                data={
                    "thread_id": thread_id,
                    "status": "failed",
                    "message": f"工作流执行失败: {error_msg}",
                    "error": error_msg
                }
            )

        else:
            # 其他状态（不应该出现，因为正常流程会在 reviewing 暂停）
            update_task_status(
                db, thread_id,
                status=status,
                current_step=current_step,
                progress=50,
                result_data=result_state
            )

    except Exception as e:
        error_msg = f"异步工作流执行异常: {str(e)}\n{traceback.format_exc()}"
        print(f"[异步工作流] {error_msg}")

        update_task_status(
            db, thread_id,
            status="failed",
            current_step="execution_error",
            progress=0,
            error_message=error_msg
        )

        # 推送异常通知
        await send_message_to_user(
            user_id=user_id,
            message_type="workflow_error",
            data={
                "thread_id": thread_id,
                "status": "failed",
                "message": f"工作流执行异常: {str(e)}",
                "error": error_msg
            }
        )


def start_workflow_background(
    thread_id: str,
    initial_state: Dict[str, Any],
    user_id: int,
    db: Session
):
    """
    启动后台工作流任务

    Args:
        thread_id: 线程ID
        initial_state: 初始状态
        user_id: 用户ID
        db: 数据库会话
    """
    # 使用 asyncio 在后台执行
    import threading

    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                execute_workflow_async(thread_id, initial_state, user_id, db)
            )
        finally:
            loop.close()

    thread = threading.Thread(target=run_async, daemon=True)
    thread.start()

    print(f"[异步工作流] 后台任务已启动: {thread_id}")
