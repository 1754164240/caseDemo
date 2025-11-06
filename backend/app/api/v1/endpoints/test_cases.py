from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.test_case import TestCase
from app.models.test_point import TestPoint
from app.models.requirement import Requirement
from app.schemas.test_case import TestCase as TestCaseSchema, TestCaseCreate, TestCaseUpdate
from app.services.ai_service import ai_service
from app.services.websocket_service import manager
from app.services.document_parser import DocumentParser

router = APIRouter()


async def generate_test_cases_background(test_point_id: int, db: Session, user_id: int):
    """后台生成测试用例"""
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
        test_cases_data = ai_service.generate_test_cases(test_point_data, context)
        
        # 保存测试用例
        for tc_data in test_cases_data:
            test_case = TestCase(
                test_point_id=test_point_id,
                title=tc_data.get('title', ''),
                description=tc_data.get('description', ''),
                preconditions=tc_data.get('preconditions', ''),
                test_steps=tc_data.get('test_steps', []),
                expected_result=tc_data.get('expected_result', ''),
                priority=tc_data.get('priority', 'medium'),
                test_type=tc_data.get('test_type', 'functional')
            )
            db.add(test_case)
        
        db.commit()
        
        # 发送通知
        await manager.notify_test_case_generated(user_id, test_point_id, len(test_cases_data))
        
    except Exception as e:
        print(f"Error generating test cases: {e}")


@router.get("/", response_model=List[TestCaseSchema])
def read_test_cases(
    test_point_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取测试用例列表"""
    query = db.query(TestCase).join(TestPoint).join(Requirement).filter(
        Requirement.user_id == current_user.id
    )
    
    if test_point_id:
        query = query.filter(TestCase.test_point_id == test_point_id)
    
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
    
    test_case = TestCase(**test_case_in.model_dump())
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
    background_tasks.add_task(generate_test_cases_background, test_point_id, db, current_user.id)
    
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

