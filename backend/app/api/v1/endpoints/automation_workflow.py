"""自动化用例工作流 API 端点（异步模式 + 任务查询）"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.workflow_task import WorkflowTask
from app.schemas.automation import (
    CreateCaseWorkflowRequest,
    HumanReviewRequest,
    WorkflowStateResponse,
    WorkflowResultResponse
)
from app.services.automation_workflow_service import AutomationWorkflowService
from app.services.async_workflow_executor import start_workflow_background, update_task_status


router = APIRouter()


@router.post("/workflow/start")
async def start_automation_workflow(
    request: CreateCaseWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    启动自动化用例生成工作流（异步模式）

    工作流将在后台异步执行，立即返回任务ID。
    前端可通过 WebSocket 接收实时进度，或调用 GET /workflow/tasks/{task_id} 查询状态。

    Returns:
        任务信息，包含 task_id 和 thread_id
    """
    try:
        # 生成唯一线程 ID
        thread_id = f"workflow_{current_user.id}_{uuid.uuid4().hex[:8]}"

        print(f"[API] 用户 {current_user.username} 启动异步工作流，线程ID: {thread_id}")
        print(f"[API] 测试用例ID: {request.test_case_id}")

        # 准备初始状态
        initial_state = {
            "test_case_id": request.test_case_id,
            "name": request.name,
            "module_id": request.module_id,
            "scene_id": request.scene_id,
            "scenario_type": request.scenario_type or "API",
            "description": request.description or "",
        }

        # 创建任务记录
        task = WorkflowTask(
            thread_id=thread_id,
            task_type="automation_case",
            user_id=current_user.id,
            test_case_id=request.test_case_id,
            status="pending",
            current_step="initializing",
            progress=0,
            input_params=initial_state,
            need_review=False
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        print(f"[API] 任务记录已创建，ID: {task.id}")

        # 启动后台工作流
        start_workflow_background(
            thread_id=thread_id,
            initial_state=initial_state,
            user_id=current_user.id,
            db=db
        )

        return {
            "task_id": task.id,
            "thread_id": thread_id,
            "status": "pending",
            "message": "工作流已启动，正在后台执行...",
            "test_case_id": request.test_case_id
        }

    except Exception as e:
        print(f"[API] 启动异步工作流失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"启动工作流失败: {str(e)}"
        )


@router.get("/workflow/tasks/{task_id}")
async def get_workflow_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    查询工作流任务状态

    Args:
        task_id: 任务ID

    Returns:
        任务详细信息
    """
    try:
        task = db.query(WorkflowTask).filter(
            WorkflowTask.id == task_id,
            WorkflowTask.user_id == current_user.id
        ).first()

        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"未找到任务 {task_id} 或无权访问"
            )

        return task.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] 查询任务失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"查询任务失败: {str(e)}"
        )


@router.get("/workflow/tasks")
async def list_workflow_tasks(
    status: Optional[str] = Query(None, description="按状态筛选: pending/processing/reviewing/completed/failed"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    查询当前用户的工作流任务列表

    Args:
        status: 任务状态筛选
        limit: 每页数量
        offset: 偏移量

    Returns:
        任务列表
    """
    try:
        query = db.query(WorkflowTask).filter(WorkflowTask.user_id == current_user.id)

        if status:
            query = query.filter(WorkflowTask.status == status)

        # 按创建时间倒序
        query = query.order_by(WorkflowTask.created_at.desc())

        total = query.count()
        tasks = query.limit(limit).offset(offset).all()

        return {
            "total": total,
            "items": [task.to_dict() for task in tasks],
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        print(f"[API] 查询任务列表失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"查询任务列表失败: {str(e)}"
        )


@router.post("/workflow/{thread_id}/review", response_model=WorkflowResultResponse)
async def submit_human_review(
    thread_id: str,
    request: HumanReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    提交人工审核结果并继续执行工作流（使用 LangGraph Command(resume=...)）

    Args:
        thread_id: 工作流线程 ID（从 start_workflow 返回）
        request: 审核请求
            - review_status: approved（通过）/ modified（修改后通过）/ rejected（拒绝重新生成）
            - corrected_body: 修正后的测试数据（可选）
            - feedback: 反馈意见（可选）

    Returns:
        最终执行结果，包含创建的用例信息
    """
    try:
        # 验证任务存在且属于当前用户
        task = db.query(WorkflowTask).filter(
            WorkflowTask.thread_id == thread_id,
            WorkflowTask.user_id == current_user.id
        ).first()

        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"未找到工作流任务或无权访问"
            )

        if task.status != "reviewing":
            raise HTTPException(
                status_code=400,
                detail=f"任务状态不是 reviewing，当前状态: {task.status}"
            )

        # 创建工作流服务
        workflow_svc = AutomationWorkflowService(db)

        print(f"[API] 用户 {current_user.username} 提交审核: {request.review_status}")

        # 更新任务状态
        update_task_status(
            db, thread_id,
            status="processing",
            current_step="processing_review",
            progress=85
        )

        # 使用 LangGraph resume 继续执行工作流
        final_state = workflow_svc.resume_workflow(
            thread_id=thread_id,
            review_status=request.review_status,
            corrected_body=request.corrected_body,
            feedback=request.feedback
        )

        if not final_state:
            raise HTTPException(
                status_code=404,
                detail=f"未找到工作流 {thread_id}，可能已过期或不存在"
            )

        status = final_state.get("status", "unknown")
        current_step = final_state.get("current_step", "unknown")

        print(f"[API] 工作流最终状态: {status}, 步骤: {current_step}")

        # 更新任务最终状态
        update_task_status(
            db, thread_id,
            status=status,
            current_step=current_step,
            progress=100 if status == "completed" else 0,
            new_usercase_id=final_state.get("new_usercase_id"),
            created_case=final_state.get("created_case"),
            error_message=final_state.get("error"),
            result_data=final_state
        )

        # 检查是否成功完成
        if status == "completed":
            print(f"[API] 用例创建成功! ID: {final_state.get('new_usercase_id')}")
        elif status == "failed":
            print(f"[API] 工作流失败: {final_state.get('error')}")

        return WorkflowResultResponse(
            thread_id=thread_id,
            status=status,
            current_step=current_step,
            created_case=final_state.get("created_case"),
            new_usercase_id=final_state.get("new_usercase_id"),
            error=final_state.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] 提交审核失败: {e}")
        import traceback
        traceback.print_exc()

        # 更新任务为失败状态
        update_task_status(
            db, thread_id,
            status="failed",
            error_message=f"提交审核失败: {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"提交审核失败: {str(e)}"
        )


@router.get("/workflow/{thread_id}/state", response_model=WorkflowStateResponse)
async def get_workflow_state(
    thread_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    查询工作流当前状态（从 LangGraph 获取）

    Args:
        thread_id: 工作流线程 ID

    Returns:
        工作流当前状态
    """
    try:
        # 验证任务存在且属于当前用户
        task = db.query(WorkflowTask).filter(
            WorkflowTask.thread_id == thread_id,
            WorkflowTask.user_id == current_user.id
        ).first()

        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"未找到工作流任务或无权访问"
            )

        workflow_svc = AutomationWorkflowService(db)
        state = workflow_svc.get_state(thread_id)

        if not state:
            # 如果 LangGraph 没有状态，返回任务记录的状态
            return WorkflowStateResponse(
                thread_id=thread_id,
                status=task.status,
                current_step=task.current_step or "unknown",
                need_human_review=task.need_review,
                state={
                    "status": task.status,
                    "current_step": task.current_step,
                    "progress": task.progress,
                    "error": task.error_message
                }
            )

        status = state.get("status", "unknown")
        current_step = state.get("current_step", "unknown")
        need_review = status == "reviewing"

        return WorkflowStateResponse(
            thread_id=thread_id,
            status=status,
            current_step=current_step,
            need_human_review=need_review,
            state=state
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] 获取工作流状态失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取工作流状态失败: {str(e)}"
        )


@router.get("/workflow/{thread_id}/validation")
async def get_workflow_validation_result(
    thread_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取工作流的数据校验结果

    Args:
        thread_id: 工作流线程 ID

    Returns:
        校验结果详情
    """
    try:
        # 验证任务存在且属于当前用户
        task = db.query(WorkflowTask).filter(
            WorkflowTask.thread_id == thread_id,
            WorkflowTask.user_id == current_user.id
        ).first()

        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"未找到工作流任务或无权访问"
            )

        workflow_svc = AutomationWorkflowService(db)
        state = workflow_svc.get_state(thread_id)

        if not state:
            return {
                "has_validation": False,
                "message": "工作流尚未执行到校验阶段"
            }

        validation_result = state.get("validation_result")

        if not validation_result:
            return {
                "has_validation": False,
                "message": "工作流尚未执行到校验阶段"
            }

        return {
            "has_validation": True,
            "validation_result": validation_result,
            "validation_errors": state.get("validation_errors", []),
            "generated_body": state.get("generated_body", []),
            "field_metadata": state.get("field_metadata", {})
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] 获取校验结果失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取校验结果失败: {str(e)}"
        )
