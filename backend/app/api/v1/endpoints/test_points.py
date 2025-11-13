from typing import List, Optional, Dict
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db, SessionLocal
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.test_point import TestPoint
from app.models.test_case import TestCase
from app.models.requirement import Requirement, RequirementStatus
from app.models.test_point_history import TestPointHistory
from app.schemas.test_point import (
    TestPoint as TestPointSchema,
    TestPointCreate,
    TestPointUpdate,
    TestPointWithCases,
    TestPointApproval,
    TestPointOptimizeRequest,
    TestPointHistoryEntry,
    TestPointBulkUpdateRequest,
)
from app.services.ai_service import get_ai_service
from app.services.websocket_service import manager
from app.services.document_parser import DocumentParser
from app.services.document_embedding_service import document_embedding_service
from app.core.config import settings

router = APIRouter()


def _run_async_notification(loop: Optional[asyncio.AbstractEventLoop], coro, description: str):
    """在线程池任务中安全地调度异步通知"""
    if not loop:
        return
    try:
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        future.result()
    except Exception as notify_error:
        print(f"[WARNING] {description}: {notify_error}")


def generate_test_point_code(db: Session) -> str:
    """生成测试点编号"""
    # 获取当前最大编号
    max_code = db.query(func.max(TestPoint.code)).scalar()
    if max_code:
        # 提取数字部分并加1
        try:
            num = int(max_code.split('-')[1])
            return f"TP-{num + 1:03d}"
        except:
            pass
    # 如果没有现有编号或解析失败，从 001 开始
    return "TP-001"


def _extract_code_number(code: Optional[str]) -> int:
    if not code:
        return 0
    try:
        parts = code.split('-')
        return int(parts[-1])
    except Exception:
        digits = ''.join(ch for ch in code if ch.isdigit())
        return int(digits) if digits else 0


def _ensure_regeneration_allowed(db: Session, requirement_id: int, force: bool) -> None:
    """在重新生成前验证是否存在已使用的测试点"""
    case_count = (
        db.query(func.count(TestCase.id))
        .join(TestPoint, TestCase.test_point_id == TestPoint.id)
        .filter(TestPoint.requirement_id == requirement_id)
        .scalar()
    )
    approved_count = (
        db.query(func.count(TestPoint.id))
        .filter(
            TestPoint.requirement_id == requirement_id,
            TestPoint.approval_status == "approved",
        )
        .scalar()
    )
    if (case_count > 0 or approved_count > 0) and not force:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "test_points_in_use",
                "cases": case_count,
                "approved": approved_count,
                "message": (
                    f"检测到该需求已有 {case_count} 条关联测试用例或 {approved_count} 条已审批测试点，"
                    "若继续重新生成将会清理这些数据，请确认后重试。"
                ),
            },
        )


def _record_history_entry(
    db: Session,
    test_point: TestPoint,
    prompt_summary: str,
    operator_id: Optional[int],
    status: str = "pending",
) -> None:
    version_count = (
        db.query(func.count(TestPointHistory.id))
        .filter(TestPointHistory.test_point_id == test_point.id)
        .scalar()
        or 0
    )
    version_label = f"v{version_count + 1:03d}"
    history = TestPointHistory(
        test_point_id=test_point.id,
        requirement_id=test_point.requirement_id,
        version=version_label,
        title=test_point.title,
        description=test_point.description,
        category=test_point.category,
        priority=test_point.priority,
        business_line=test_point.business_line,
        prompt_summary=prompt_summary,
        status=status,
        operator_id=operator_id,
    )
    db.add(history)


def _build_prompt_summary(
    batch_prompt: Optional[str],
    per_prompt: Optional[str],
    business_info: Optional[str],
    version_note: Optional[str],
) -> str:
    sections: List[str] = []
    if per_prompt:
        sections.append(f"单点提示：{per_prompt}")
    if batch_prompt:
        sections.append(f"整体提示：{batch_prompt}")
    if business_info:
        sections.append(f"业务信息：{business_info}")
    if version_note:
        sections.append(f"版本备注：{version_note}")
    return "\n".join(sections).strip()


def _assemble_single_prompt_text(
    requirement_text: str,
    test_point: TestPoint,
    per_prompt: Optional[str],
    payload: TestPointOptimizeRequest,
) -> str:
    context = requirement_text[: settings.TEST_POINT_MAX_INPUT_CHARS]
    blocks = [
        context,
        "当前测试点：",
        f"标题：{test_point.title}",
        f"描述：{test_point.description or ''}",
        f"分类：{test_point.category or ''}",
        f"业务线：{test_point.business_line or ''}",
        f"优先级：{test_point.priority or ''}",
    ]
    if payload.business_info:
        blocks.append(f"业务背景：{payload.business_info}")
    if payload.batch_prompt:
        blocks.append(f"整体提示词：{payload.batch_prompt}")
    if per_prompt:
        blocks.append(f"单点提示词：{per_prompt}")
    blocks.append("请输出优化后的测试点（JSON 列表）。")
    return "\n".join(blocks)


def _assemble_batch_prompt_text(
    requirement_text: str,
    points: List[TestPoint],
    payload: TestPointOptimizeRequest,
) -> str:
    context = requirement_text[: settings.TEST_POINT_MAX_INPUT_CHARS]
    summary = "\n".join(
        f"- [{tp.code}] {tp.title}：{(tp.description or '')[:200]}"
        for tp in points
    )
    blocks = [
        context,
        "待整体优化的测试点：",
        summary,
    ]
    if payload.business_info:
        blocks.append(f"业务背景：{payload.business_info}")
    if payload.batch_prompt:
        blocks.append(f"整体提示词：{payload.batch_prompt}")
    blocks.append("请输出与原数量一致的优化测试点列表（JSON）。")
    return "\n".join(blocks)


def regenerate_test_points_background(
    requirement_id: int,
    user_feedback: str,
    user_id: int,
    force: bool = False,
    loop: Optional[asyncio.AbstractEventLoop] = None
):
    """重新生成测试点后台任务"""
    db = SessionLocal()
    try:
        requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
        if not requirement:
            return

        requirement.status = RequirementStatus.PROCESSING
        db.commit()

        print(f"[INFO] 开始重新生成测试点，需求ID: {requirement_id}, force={force}")

        text = DocumentParser.parse(requirement.file_path, requirement.file_type.value)
        if not text:
            raise ValueError("解析需求文档失败")

        quality = DocumentParser.evaluate_quality(text)
        print(
            "[INFO] 文档质量分析："
            f"总字符数 {len(text)}，有效字符 {quality['meaningful_chars']}, "
            f"非空行比例 {quality['non_empty_ratio']:.2%}"
        )
        if quality["meaningful_chars"] < settings.MIN_REQUIREMENT_CHARACTERS:
            raise ValueError("需求文档字符数不足")
        if quality["non_empty_ratio"] < settings.MIN_NON_EMPTY_LINE_RATIO:
            raise ValueError("需求文档内容过于稀疏")

        chunks = document_embedding_service.split_text(text)
        ai_context = document_embedding_service.build_ai_context(chunks)
        if not ai_context:
            ai_context = text[: settings.TEST_POINT_MAX_INPUT_CHARS]
            print("[WARNING] 向量检索失败，使用原始文本作为上下文")

        ai_svc = get_ai_service(db)
        test_points_data = ai_svc.extract_test_points(
            ai_context,
            user_feedback,
            allow_fallback=False,
        )

        if not test_points_data:
            raise ValueError("AI 未能生成测试点")

        print(f"[INFO] 成功生成 {len(test_points_data)} 个测试点")

        latest_code_value = db.query(func.max(TestPoint.code)).scalar()
        next_code_num = _extract_code_number(latest_code_value)

        def allocate_code() -> str:
            nonlocal next_code_num
            next_code_num += 1
            return f"TP-{next_code_num:03d}"

        new_test_points: List[TestPoint] = []
        for tp_data in test_points_data:
            new_test_points.append(
                TestPoint(
                    requirement_id=requirement_id,
                    code=allocate_code(),
                    title=tp_data.get('title', ''),
                    description=tp_data.get('description', ''),
                    category=tp_data.get('category', ''),
                    priority=tp_data.get('priority', 'medium'),
                    business_line=tp_data.get('business_line', ''),
                    user_feedback=user_feedback,
                )
            )

        existing_point_ids = [
            tp.id
            for tp in db.query(TestPoint.id).filter(TestPoint.requirement_id == requirement_id).all()
        ]
        if existing_point_ids:
            db.query(TestCase).filter(TestCase.test_point_id.in_(existing_point_ids)).delete(
                synchronize_session=False
            )
            db.query(TestPointHistory).filter(TestPointHistory.test_point_id.in_(existing_point_ids)).delete(
                synchronize_session=False
            )
            db.query(TestPoint).filter(TestPoint.id.in_(existing_point_ids)).delete(synchronize_session=False)

        db.add_all(new_test_points)

        requirement.status = RequirementStatus.COMPLETED
        db.commit()

        print(f"[INFO] 测试点重新生成完成，需求ID: {requirement_id}")

        _run_async_notification(
            loop,
            manager.notify_test_point_generated(user_id, requirement_id, len(test_points_data)),
            "发送测试点生成通知失败"
        )

    except Exception as e:
        print(f"[ERROR] 重新生成测试点失败: {e}")
        import traceback
        traceback.print_exc()

        try:
            requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
            if requirement:
                requirement.status = RequirementStatus.FAILED
                db.commit()
        except Exception as update_error:
            print(f"[ERROR] 更新需求状态失败: {update_error}")
    finally:
        db.close()


def _apply_candidate_to_point(
    db: Session,
    test_point: TestPoint,
    candidate: Dict[str, str],
    payload: TestPointOptimizeRequest,
    per_prompt: Optional[str],
    operator_id: Optional[int],
) -> None:
    test_point.title = candidate.get("title") or test_point.title
    test_point.description = (
        candidate.get("description")
        or candidate.get("content")
        or test_point.description
    )
    test_point.category = candidate.get("category") or test_point.category
    test_point.priority = candidate.get("priority") or test_point.priority
    test_point.business_line = candidate.get("business_line") or test_point.business_line
    test_point.approval_status = "pending"
    test_point.is_approved = False

    prompt_summary = _build_prompt_summary(
        payload.batch_prompt,
        per_prompt,
        payload.business_info,
        payload.version_note,
    )
    test_point.user_feedback = prompt_summary
    db.flush()
    _record_history_entry(db, test_point, prompt_summary, operator_id, status="pending")


def optimize_test_points_background(
    payload: TestPointOptimizeRequest,
    user_id: int,
    loop: Optional[asyncio.AbstractEventLoop] = None,
) -> None:
    db = SessionLocal()
    try:
        requirement = (
            db.query(Requirement)
            .filter(Requirement.id == payload.requirement_id)
            .first()
        )
        if not requirement:
            return

        points = (
            db.query(TestPoint)
            .filter(
                TestPoint.requirement_id == requirement.id,
                TestPoint.id.in_(payload.selected_ids),
            )
            .order_by(TestPoint.id)
            .all()
        )
        if not points:
            return

        requirement.status = RequirementStatus.PROCESSING
        db.commit()

        try:
            requirement_text = DocumentParser.parse(
                requirement.file_path, requirement.file_type.value
            )
        except Exception as parse_error:
            print(f"[WARNING] 解析需求文档失败（优化测试点）：{parse_error}")
            requirement_text = ""
        if not requirement_text:
            requirement_text = "\n".join((tp.description or "") for tp in points)

        ai_svc = get_ai_service(db)
        updated_ids: List[int] = []

        if payload.mode == "batch":
            prompt_text = _assemble_batch_prompt_text(requirement_text, points, payload)
            try:
                batch_candidates = ai_svc.extract_test_points(
                    prompt_text,
                    user_feedback=payload.batch_prompt or payload.business_info or "",
                    allow_fallback=True,
                )
            except Exception as ai_error:
                print(f"[ERROR] 批量优化失败: {ai_error}")
                batch_candidates = []
            for tp, candidate in zip(points, batch_candidates):
                if not candidate:
                    continue
                per_prompt = payload.per_point_prompts.get(tp.id)
                _apply_candidate_to_point(db, tp, candidate, payload, per_prompt, user_id)
                updated_ids.append(tp.id)
        else:
            for tp in points:
                per_prompt = payload.per_point_prompts.get(tp.id)
                prompt_text = _assemble_single_prompt_text(
                    requirement_text, tp, per_prompt, payload
                )
                try:
                    results = ai_svc.extract_test_points(
                        prompt_text,
                        user_feedback=per_prompt or payload.batch_prompt or "",
                        allow_fallback=True,
                    )
                except Exception as ai_error:
                    print(f"[ERROR] 单点优化失败: {ai_error}")
                    continue
                if not results:
                    continue
                candidate = results[0]
                _apply_candidate_to_point(db, tp, candidate, payload, per_prompt, user_id)
                updated_ids.append(tp.id)

        requirement.status = RequirementStatus.COMPLETED
        db.commit()

        if updated_ids:
            _run_async_notification(
                loop,
                manager.notify_progress(
                    user_id,
                    "test_points_optimize",
                    100,
                    f"测试点优化完成，共更新 {len(updated_ids)} 条",
                ),
                "发送优化进度失败",
            )
            _run_async_notification(
                loop,
                manager.notify_test_point_generated(
                    user_id, requirement.id, len(updated_ids)
                ),
                "发送测试点优化通知失败",
            )
    except Exception as opt_error:
        print(f"[ERROR] 优化测试点失败: {opt_error}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()

@router.get("/", response_model=List[TestPointWithCases])
def read_test_points(
    requirement_id: int = None,
    search: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取测试点列表"""
    query = db.query(TestPoint).join(Requirement).filter(
        Requirement.user_id == current_user.id
    )

    if requirement_id:
        query = query.filter(TestPoint.requirement_id == requirement_id)

    # 搜索功能
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (TestPoint.title.ilike(search_pattern)) |
            (TestPoint.description.ilike(search_pattern)) |
            (TestPoint.category.ilike(search_pattern))
        )

    # 按创建时间倒序排序
    query = query.order_by(TestPoint.created_at.desc())

    test_points = query.offset(skip).limit(limit).all()

    result = []
    for tp in test_points:
        tp_dict = TestPointWithCases.model_validate(tp)
        tp_dict.test_cases_count = len(tp.test_cases)
        result.append(tp_dict)

    return result


@router.get("/{test_point_id}", response_model=TestPointSchema)
def read_test_point(
    test_point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取测试点详情"""
    test_point = db.query(TestPoint).join(Requirement).filter(
        TestPoint.id == test_point_id,
        Requirement.user_id == current_user.id
    ).first()
    
    if not test_point:
        raise HTTPException(status_code=404, detail="Test point not found")
    
    return test_point


@router.post("/", response_model=TestPointSchema)
def create_test_point(
    test_point_in: TestPointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """手动创建测试点"""
    # 验证需求是否属于当前用户
    requirement = db.query(Requirement).filter(
        Requirement.id == test_point_in.requirement_id,
        Requirement.user_id == current_user.id
    ).first()

    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # 生成编号
    code = generate_test_point_code(db)

    test_point = TestPoint(**test_point_in.model_dump(), code=code)
    db.add(test_point)
    db.commit()
    db.refresh(test_point)

    return test_point


@router.put("/{test_point_id}", response_model=TestPointSchema)
def update_test_point(
    test_point_id: int,
    test_point_in: TestPointUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新测试点"""
    test_point = db.query(TestPoint).join(Requirement).filter(
        TestPoint.id == test_point_id,
        Requirement.user_id == current_user.id
    ).first()
    
    if not test_point:
        raise HTTPException(status_code=404, detail="Test point not found")
    
    update_data = test_point_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(test_point, field, value)
    
    db.commit()
    db.refresh(test_point)
    
    return test_point


@router.post("/{test_point_id}/feedback")
async def submit_feedback(
    test_point_id: int,
    background_tasks: BackgroundTasks,
    feedback: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """提交测试点反馈并重新生成"""
    test_point = db.query(TestPoint).join(Requirement).filter(
        TestPoint.id == test_point_id,
        Requirement.user_id == current_user.id
    ).first()
    
    if not test_point:
        raise HTTPException(status_code=404, detail="Test point not found")
    
    # 保存反馈
    test_point.user_feedback = feedback
    db.commit()

    _ensure_regeneration_allowed(db, test_point.requirement_id, force=False)
    
    # 后台重新生成测试点
    loop = asyncio.get_running_loop()
    background_tasks.add_task(
        regenerate_test_points_background,
        test_point.requirement_id,
        feedback,
        current_user.id,
        False,
        loop
    )
    
    return {"message": "Feedback submitted, regenerating test points..."}


@router.post("/regenerate/{requirement_id}")
async def regenerate_test_points(
    requirement_id: int,
    background_tasks: BackgroundTasks,
    feedback: Optional[str] = None,
    force: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """重新生成需求的测试点"""
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.user_id == current_user.id
    ).first()

    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    _ensure_regeneration_allowed(db, requirement_id, force)

    loop = asyncio.get_running_loop()
    background_tasks.add_task(
        regenerate_test_points_background,
        requirement_id,
        feedback or "",
        current_user.id,
        force,
        loop
    )

    return {"message": "Regenerating test points..."}


@router.post("/optimize")
async def optimize_test_points(
    payload: TestPointOptimizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """使用 LangGraph + LangChain 优化测试点"""
    requirement = (
        db.query(Requirement)
        .filter(
            Requirement.id == payload.requirement_id,
            Requirement.user_id == current_user.id,
        )
        .first()
    )
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    if not payload.selected_ids:
        raise HTTPException(status_code=400, detail="请选择测试点")

    valid_ids = {
        tp.id
        for tp in db.query(TestPoint.id)
        .filter(
            TestPoint.requirement_id == requirement.id,
            TestPoint.id.in_(payload.selected_ids),
        )
        .all()
    }
    missing = [tp_id for tp_id in payload.selected_ids if tp_id not in valid_ids]
    if missing:
        raise HTTPException(status_code=400, detail="部分测试点不存在或无权访问")

    loop = asyncio.get_running_loop()
    background_tasks.add_task(
        optimize_test_points_background,
        payload,
        current_user.id,
        loop,
    )
    return {"message": "测试点优化任务已开始"}


@router.post("/bulk-update")
def bulk_update_test_points(
    payload: TestPointBulkUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """批量保存测试点"""
    if not payload.updates:
        return {"updated": 0}

    requirement = (
        db.query(Requirement)
        .filter(
            Requirement.id == payload.requirement_id,
            Requirement.user_id == current_user.id,
        )
        .first()
    )
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    mapping = {
        tp.id: tp
        for tp in db.query(TestPoint)
        .filter(
            TestPoint.requirement_id == requirement.id,
            TestPoint.id.in_([item.id for item in payload.updates]),
        )
        .all()
    }

    updated = 0
    for item in payload.updates:
        tp = mapping.get(item.id)
        if not tp:
            continue
        if item.title is not None:
            tp.title = item.title
        if item.description is not None:
            tp.description = item.description
        if item.category is not None:
            tp.category = item.category
        if item.priority is not None:
            tp.priority = item.priority
        if item.business_line is not None:
            tp.business_line = item.business_line
        if item.user_feedback is not None:
            tp.user_feedback = item.user_feedback
        if item.approval_status is not None:
            tp.approval_status = item.approval_status
            tp.is_approved = (item.approval_status == "approved")
        updated += 1

    db.commit()
    return {"updated": updated}


@router.get("/{test_point_id}/history", response_model=List[TestPointHistoryEntry])
def get_test_point_history(
    test_point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取测试点历史"""
    test_point = (
        db.query(TestPoint)
        .join(Requirement)
        .filter(
            TestPoint.id == test_point_id,
            Requirement.user_id == current_user.id,
        )
        .first()
    )
    if not test_point:
        raise HTTPException(status_code=404, detail="Test point not found")

    histories = (
        db.query(TestPointHistory)
        .filter(TestPointHistory.test_point_id == test_point_id)
        .order_by(TestPointHistory.created_at.desc())
        .all()
    )
    return histories


@router.delete("/{test_point_id}")
def delete_test_point(
    test_point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除测试点"""
    test_point = db.query(TestPoint).join(Requirement).filter(
        TestPoint.id == test_point_id,
        Requirement.user_id == current_user.id
    ).first()

    if not test_point:
        raise HTTPException(status_code=404, detail="Test point not found")

    db.delete(test_point)
    db.commit()

    return {"message": "Test point deleted successfully"}


@router.post("/{test_point_id}/approve", response_model=TestPointSchema)
def approve_test_point(
    test_point_id: int,
    approval: TestPointApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """审批测试点"""
    # 验证审批状态
    if approval.approval_status not in ['approved', 'rejected']:
        raise HTTPException(status_code=400, detail="Invalid approval status. Must be 'approved' or 'rejected'")

    # 查询测试点
    test_point = db.query(TestPoint).join(Requirement).filter(
        TestPoint.id == test_point_id,
        Requirement.user_id == current_user.id
    ).first()

    if not test_point:
        raise HTTPException(status_code=404, detail="Test point not found")

    # 更新审批信息
    test_point.approval_status = approval.approval_status
    test_point.approved_by = current_user.id
    test_point.approved_at = func.now()
    test_point.approval_comment = approval.approval_comment

    # 同步更新 is_approved 字段（用于兼容性）
    test_point.is_approved = (approval.approval_status == 'approved')

    db.commit()
    db.refresh(test_point)

    return test_point


@router.post("/{test_point_id}/reset-approval", response_model=TestPointSchema)
def reset_test_point_approval(
    test_point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """重置测试点审批状态"""
    test_point = db.query(TestPoint).join(Requirement).filter(
        TestPoint.id == test_point_id,
        Requirement.user_id == current_user.id
    ).first()

    if not test_point:
        raise HTTPException(status_code=404, detail="Test point not found")

    # 重置审批信息
    test_point.approval_status = 'pending'
    test_point.approved_by = None
    test_point.approved_at = None
    test_point.approval_comment = None
    test_point.is_approved = False

    db.commit()
    db.refresh(test_point)

    return test_point

