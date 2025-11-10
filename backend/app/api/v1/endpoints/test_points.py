from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.test_point import TestPoint
from app.models.test_case import TestCase
from app.models.requirement import Requirement, RequirementStatus
from app.schemas.test_point import TestPoint as TestPointSchema, TestPointCreate, TestPointUpdate, TestPointWithCases, TestPointApproval
from app.services.ai_service import get_ai_service
from app.services.websocket_service import manager
from app.services.document_parser import DocumentParser

router = APIRouter()


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


async def regenerate_test_points_background(requirement_id: int, user_feedback: str, db: Session, user_id: int):
    """后台重新生成测试点"""
    try:
        requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
        if not requirement:
            return

        # 更新状态为处理中
        requirement.status = RequirementStatus.PROCESSING
        db.commit()

        print(f"[INFO] 开始重新生成测试点，需求 ID: {requirement_id}")

        # 解析文档
        text = DocumentParser.parse(requirement.file_path, requirement.file_type.value)
        if not text:
            raise Exception("Failed to parse document")

        print(f"[INFO] 文档解析成功，文本长度: {len(text)}")

        # 使用 AI 重新生成测试点（带用户反馈）
        ai_svc = get_ai_service(db)
        test_points_data = ai_svc.extract_test_points(text, user_feedback)

        print(f"[INFO] 成功生成 {len(test_points_data)} 个测试点")

        # 保存新的测试点
        for tp_data in test_points_data:
            code = generate_test_point_code(db)
            test_point = TestPoint(
                requirement_id=requirement_id,
                code=code,
                title=tp_data.get('title', ''),
                description=tp_data.get('description', ''),
                category=tp_data.get('category', ''),
                priority=tp_data.get('priority', 'medium'),
                business_line=tp_data.get('business_line', ''),
                user_feedback=user_feedback
            )
            db.add(test_point)
            db.flush()  # 确保编号被保存，以便下一个测试点能获取正确的编号

        # 更新需求状态为已完成
        requirement.status = RequirementStatus.COMPLETED
        db.commit()

        print(f"[INFO] 测试点重新生成完成，需求 ID: {requirement_id}")

        # 发送通知
        await manager.notify_test_point_generated(user_id, requirement_id, len(test_points_data))

    except Exception as e:
        print(f"[ERROR] 重新生成测试点失败: {e}")
        import traceback
        traceback.print_exc()

        # 更新状态为失败
        try:
            requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
            if requirement:
                requirement.status = RequirementStatus.FAILED
                db.commit()
        except Exception as update_error:
            print(f"[ERROR] 更新状态失败: {update_error}")


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
    
    # 后台重新生成测试点
    background_tasks.add_task(
        regenerate_test_points_background,
        test_point.requirement_id,
        feedback,
        db,
        current_user.id
    )
    
    return {"message": "Feedback submitted, regenerating test points..."}


@router.post("/regenerate/{requirement_id}")
async def regenerate_test_points(
    requirement_id: int,
    background_tasks: BackgroundTasks,
    feedback: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """重新生成需求的测试点"""
    # 验证需求是否属于当前用户
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.user_id == current_user.id
    ).first()

    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # 获取该需求下的所有测试点ID
    test_point_ids = [tp.id for tp in db.query(TestPoint).filter(TestPoint.requirement_id == requirement_id).all()]

    # 先删除所有相关的测试用例
    if test_point_ids:
        db.query(TestCase).filter(TestCase.test_point_id.in_(test_point_ids)).delete(synchronize_session=False)

    # 再删除该需求下的所有旧测试点
    db.query(TestPoint).filter(TestPoint.requirement_id == requirement_id).delete(synchronize_session=False)
    db.commit()

    # 后台重新生成测试点
    background_tasks.add_task(
        regenerate_test_points_background,
        requirement_id,
        feedback or "",
        db,
        current_user.id
    )

    return {"message": "Regenerating test points..."}


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

