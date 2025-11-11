from typing import List, Optional
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db, SessionLocal
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.test_case import TestCase
from app.models.test_point import TestPoint
from app.models.requirement import Requirement
from app.schemas.test_case import TestCase as TestCaseSchema, TestCaseCreate, TestCaseUpdate, TestCaseApproval
from app.services.ai_service import get_ai_service
from app.services.websocket_service import manager
from app.services.document_parser import DocumentParser

router = APIRouter()


def _run_async_notification(loop: Optional[asyncio.AbstractEventLoop], coro, description: str):
    """在线程池中运行的任务里安全地发送异步通知"""
    if not loop:
        return
    try:
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        future.result()
    except Exception as notify_error:
        print(f"[WARNING] {description}: {notify_error}")


def generate_test_case_code(db: Session, test_point: TestPoint) -> str:
    """生成测试用例编号"""
    # 获取该测试点下的测试用例数量
    count = db.query(func.count(TestCase.id)).filter(
        TestCase.test_point_id == test_point.id
    ).scalar()

    # 生成编号：测试点编号-序号
    return f"{test_point.code}-{count + 1}"


def generate_test_cases_background(
    test_point_id: int,
    user_id: int,
    loop: Optional[asyncio.AbstractEventLoop] = None
):
    """后台生成测试用例（在线程池运行）"""
    db = SessionLocal()
    try:
        test_point = db.query(TestPoint).filter(TestPoint.id == test_point_id).first()
        if not test_point:
            return
        
        requirement = db.query(Requirement).filter(Requirement.id == test_point.requirement_id).first()
        if not requirement:
            return
        
        # 解析需求文档获取上下文
        context = DocumentParser.parse(requirement.file_path, requirement.file_type.value)
        
        # 准备测试点数据
        test_point_data = {
            'title': test_point.title,
            'description': test_point.description,
            'category': test_point.category,
            'priority': test_point.priority
        }
        
        # 使用 AI 生成测试用例
        ai_svc = get_ai_service(db)
        test_cases_data = ai_svc.generate_test_cases(test_point_data, context)
        
        # 保存测试用例
        for tc_data in test_cases_data:
            code = generate_test_case_code(db, test_point)
            test_case = TestCase(
                test_point_id=test_point_id,
                code=code,
                title=tc_data.get('title', ''),
                description=tc_data.get('description', ''),
                preconditions=tc_data.get('preconditions', ''),
                test_steps=tc_data.get('test_steps', []),
                expected_result=tc_data.get('expected_result', ''),
                priority=tc_data.get('priority', 'medium'),
                test_type=tc_data.get('test_type', 'functional')
            )
            db.add(test_case)
            db.flush()  # 确保编号被保存

        db.commit()
        
        # 发送通知
        _run_async_notification(
            loop,
            manager.notify_test_case_generated(user_id, test_point_id, len(test_cases_data)),
            "发送测试用例生成通知失败"
        )
        
    except Exception as e:
        db.rollback()
        print(f"[ERROR] 生成测试用例失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


@router.get("/", response_model=List[TestCaseSchema])
def read_test_cases(
    requirement_id: int = None,
    test_point_id: int = None,
    search: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取测试用例列表"""
    query = db.query(TestCase).join(TestPoint).join(Requirement).filter(
        Requirement.user_id == current_user.id
    )

    # 按需求筛选
    if requirement_id:
        query = query.filter(Requirement.id == requirement_id)

    # 按测试点筛选
    if test_point_id:
        query = query.filter(TestCase.test_point_id == test_point_id)

    # 搜索功能
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (TestCase.title.ilike(search_pattern)) |
            (TestCase.description.ilike(search_pattern)) |
            (TestCase.preconditions.ilike(search_pattern)) |
            (TestCase.expected_result.ilike(search_pattern))
        )

    test_cases = query.offset(skip).limit(limit).all()
    return test_cases


@router.get("/{test_case_id}", response_model=TestCaseSchema)
def read_test_case(
    test_case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取测试用例详情"""
    test_case = db.query(TestCase).join(TestPoint).join(Requirement).filter(
        TestCase.id == test_case_id,
        Requirement.user_id == current_user.id
    ).first()
    
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    return test_case


@router.post("/", response_model=TestCaseSchema)
def create_test_case(
    test_case_in: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """手动创建测试用例"""
    # 验证测试点是否属于当前用户
    test_point = db.query(TestPoint).join(Requirement).filter(
        TestPoint.id == test_case_in.test_point_id,
        Requirement.user_id == current_user.id
    ).first()

    if not test_point:
        raise HTTPException(status_code=404, detail="Test point not found")

    # 生成编号
    code = generate_test_case_code(db, test_point)

    test_case = TestCase(**test_case_in.model_dump(), code=code)
    db.add(test_case)
    db.commit()
    db.refresh(test_case)

    return test_case


@router.post("/generate/{test_point_id}")
async def generate_test_cases(
    test_point_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """为指定测试点生成测试用例"""
    test_point = db.query(TestPoint).join(Requirement).filter(
        TestPoint.id == test_point_id,
        Requirement.user_id == current_user.id
    ).first()
    
    if not test_point:
        raise HTTPException(status_code=404, detail="Test point not found")
    
    # 后台生成测试用例
    loop = asyncio.get_running_loop()
    background_tasks.add_task(
        generate_test_cases_background,
        test_point_id,
        current_user.id,
        loop
    )
    
    return {"message": "Generating test cases..."}


@router.put("/{test_case_id}", response_model=TestCaseSchema)
def update_test_case(
    test_case_id: int,
    test_case_in: TestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新测试用例"""
    test_case = db.query(TestCase).join(TestPoint).join(Requirement).filter(
        TestCase.id == test_case_id,
        Requirement.user_id == current_user.id
    ).first()

    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    update_data = test_case_in.model_dump(exclude_unset=True)
    # 确保不更新 code 字段（编号是自动生成的，不可修改）
    update_data.pop('code', None)

    for field, value in update_data.items():
        setattr(test_case, field, value)

    db.commit()
    db.refresh(test_case)

    return test_case


@router.delete("/{test_case_id}")
def delete_test_case(
    test_case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除测试用例"""
    test_case = db.query(TestCase).join(TestPoint).join(Requirement).filter(
        TestCase.id == test_case_id,
        Requirement.user_id == current_user.id
    ).first()
    
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    
    db.delete(test_case)
    db.commit()

    return {"message": "Test case deleted successfully"}


@router.post("/{test_case_id}/approve", response_model=TestCaseSchema)
def approve_test_case(
    test_case_id: int,
    approval: TestCaseApproval,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """审批测试用例"""
    # 验证审批状态
    if approval.approval_status not in ['approved', 'rejected']:
        raise HTTPException(status_code=400, detail="Invalid approval status. Must be 'approved' or 'rejected'")

    # 查询测试用例
    test_case = db.query(TestCase).join(TestPoint).join(Requirement).filter(
        TestCase.id == test_case_id,
        Requirement.user_id == current_user.id
    ).first()

    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    # 更新审批信息
    test_case.approval_status = approval.approval_status
    test_case.approved_by = current_user.id
    test_case.approved_at = func.now()
    test_case.approval_comment = approval.approval_comment

    db.commit()
    db.refresh(test_case)

    return test_case


@router.post("/{test_case_id}/reset-approval", response_model=TestCaseSchema)
def reset_test_case_approval(
    test_case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """重置测试用例审批状态"""
    test_case = db.query(TestCase).join(TestPoint).join(Requirement).filter(
        TestCase.id == test_case_id,
        Requirement.user_id == current_user.id
    ).first()

    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    # 重置审批信息
    test_case.approval_status = 'pending'
    test_case.approved_by = None
    test_case.approved_at = None
    test_case.approval_comment = None

    db.commit()
    db.refresh(test_case)

    return test_case

