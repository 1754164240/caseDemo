from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime
from urllib.parse import quote

from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.requirement import Requirement, FileType, RequirementStatus
from app.schemas.requirement import Requirement as RequirementSchema, RequirementCreate, RequirementUpdate, RequirementWithStats
from app.core.config import settings
from app.services.document_parser import DocumentParser
from app.services.ai_service import get_ai_service
from app.services.websocket_service import manager
from app.models.test_point import TestPoint
from sqlalchemy import func

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


async def process_requirement_background(requirement_id: int, db: Session, user_id: int):
    """后台处理需求文档"""
    requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not requirement:
        return

    try:
        # 更新状态为处理中
        requirement.status = RequirementStatus.PROCESSING
        db.commit()

        print(f"[INFO] 开始处理需求文档 ID: {requirement_id}")

        # 解析文档
        print(f"[INFO] 解析文档: {requirement.file_path}")
        text = DocumentParser.parse(requirement.file_path, requirement.file_type.value)
        if not text:
            raise Exception("Failed to parse document")

        print(f"[INFO] 文档解析成功，文本长度: {len(text)}")

        # 检查 OpenAI API Key
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "":
            print("[WARNING] OpenAI API Key 未配置，使用模拟数据")
            # 使用模拟数据
            test_points_data = [
                {
                    "title": "示例测试点 1",
                    "description": "这是一个示例测试点（OpenAI API Key 未配置）",
                    "category": "功能",
                    "priority": "high"
                },
                {
                    "title": "示例测试点 2",
                    "description": "请配置 OpenAI API Key 以使用 AI 功能",
                    "category": "功能",
                    "priority": "medium"
                }
            ]
        else:
            # 使用 AI 提取测试点
            print(f"[INFO] 调用 AI 服务提取测试点...")
            ai_service = get_ai_service(db)
            test_points_data = ai_service.extract_test_points(text)
            print(f"[INFO] AI 提取完成，测试点数量: {len(test_points_data)}")

        # 保存测试点
        for tp_data in test_points_data:
            code = generate_test_point_code(db)
            test_point = TestPoint(
                requirement_id=requirement_id,
                code=code,
                title=tp_data.get('title', ''),
                description=tp_data.get('description', ''),
                category=tp_data.get('category', ''),
                priority=tp_data.get('priority', 'medium'),
                business_line=tp_data.get('business_line', '')
            )
            db.add(test_point)
            db.flush()  # 确保编号被保存，以便下一个测试点能获取正确的编号

        db.commit()
        print(f"[INFO] 测试点保存成功")

        # 更新状态为完成
        requirement.status = RequirementStatus.COMPLETED
        db.commit()

        print(f"[INFO] 需求处理完成 ID: {requirement_id}")

        # 发送 WebSocket 通知
        await manager.notify_test_point_generated(user_id, requirement_id, len(test_points_data))

    except Exception as e:
        requirement.status = RequirementStatus.FAILED
        db.commit()
        print(f"[ERROR] 处理需求失败 ID: {requirement_id}, 错误: {str(e)}")
        import traceback
        traceback.print_exc()


@router.post("/", response_model=RequirementSchema)
async def create_requirement(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """上传需求文档"""
    # 验证文件类型
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ['docx', 'pdf', 'txt', 'xls', 'xlsx']:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # 保存文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_size = os.path.getsize(file_path)
    
    # 创建需求记录
    requirement = Requirement(
        title=title,
        description=description,
        file_name=file.filename,
        file_path=file_path,
        file_type=FileType(file_ext),
        file_size=file_size,
        user_id=current_user.id
    )
    
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    
    # 后台处理文档
    background_tasks.add_task(process_requirement_background, requirement.id, db, current_user.id)
    
    return requirement


@router.get("/", response_model=List[RequirementWithStats])
def read_requirements(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取需求列表"""
    requirements = db.query(Requirement).filter(
        Requirement.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    result = []
    for req in requirements:
        test_points_count = db.query(TestPoint).filter(TestPoint.requirement_id == req.id).count()
        test_cases_count = 0
        for tp in req.test_points:
            test_cases_count += len(tp.test_cases)
        
        req_dict = RequirementWithStats.model_validate(req)
        req_dict.test_points_count = test_points_count
        req_dict.test_cases_count = test_cases_count
        result.append(req_dict)
    
    return result


@router.get("/{requirement_id}", response_model=RequirementSchema)
def read_requirement(
    requirement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取需求详情"""
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.user_id == current_user.id
    ).first()
    
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    return requirement


@router.put("/{requirement_id}", response_model=RequirementSchema)
def update_requirement(
    requirement_id: int,
    requirement_in: RequirementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新需求"""
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.user_id == current_user.id
    ).first()
    
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    if requirement_in.title is not None:
        requirement.title = requirement_in.title
    if requirement_in.description is not None:
        requirement.description = requirement_in.description
    if requirement_in.status is not None:
        requirement.status = requirement_in.status
    
    db.commit()
    db.refresh(requirement)
    
    return requirement


@router.get("/{requirement_id}/download")
def download_requirement(
    requirement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """下载需求文档"""
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.user_id == current_user.id
    ).first()

    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # 检查文件是否存在
    if not os.path.exists(requirement.file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # 对中文文件名进行 URL 编码
    encoded_filename = quote(requirement.file_name)

    # 返回文件
    response = FileResponse(
        path=requirement.file_path,
        media_type='application/octet-stream'
    )

    # 设置 Content-Disposition header 以支持中文文件名
    # 同时提供 filename 和 filename* 两种格式以提高兼容性
    # filename: ASCII 回退（用下划线替换非 ASCII 字符）
    # filename*: RFC 5987 格式，支持 UTF-8 编码
    ascii_filename = requirement.file_name.encode('ascii', 'ignore').decode('ascii') or 'document'
    response.headers["Content-Disposition"] = (
        f"attachment; "
        f"filename=\"{ascii_filename}\"; "
        f"filename*=UTF-8''{encoded_filename}"
    )

    return response


@router.delete("/{requirement_id}")
def delete_requirement(
    requirement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除需求"""
    requirement = db.query(Requirement).filter(
        Requirement.id == requirement_id,
        Requirement.user_id == current_user.id
    ).first()

    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # 删除文件
    if os.path.exists(requirement.file_path):
        os.remove(requirement.file_path)

    db.delete(requirement)
    db.commit()

    return {"message": "Requirement deleted successfully"}

