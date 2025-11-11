from typing import List, Optional
import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime
from urllib.parse import quote

from app.db.session import get_db, SessionLocal
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.requirement import Requirement, FileType, RequirementStatus
from app.schemas.requirement import Requirement as RequirementSchema, RequirementCreate, RequirementUpdate, RequirementWithStats
from app.core.config import settings
from app.services.document_parser import DocumentParser
from app.services.document_embedding_service import document_embedding_service
from app.services.ai_service import get_ai_service
from app.services.websocket_service import manager
from app.models.test_point import TestPoint
from app.services.milvus_service import milvus_service
from sqlalchemy import func, or_

router = APIRouter()


def _run_async_notification(loop: Optional[asyncio.AbstractEventLoop], coro, description: str):
    """在后台线程中安全地调度异步通知"""
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


def cleanup_failed_requirement(
    requirement_id: int,
    file_path: str,
    db: Session,
    remove_requirement: bool = False,
):
    """删除失败需求的文件、向量与数据库记录"""
    try:
        milvus_service.delete_by_requirement(requirement_id)
        print(f"[INFO] 已清理需求 {requirement_id} 的 Milvus 向量")
    except Exception as milvus_error:
        print(f"[WARNING] 清理 Milvus 失败（需求 {requirement_id}）: {milvus_error}")

    if remove_requirement and file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"[INFO] 已删除失败需求文件: {file_path}")
        except Exception as file_error:
            print(f"[WARNING] 删除文件失败: {file_error}")

    if remove_requirement:
        try:
            requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
            if requirement:
                db.delete(requirement)
                db.commit()
                print(f"[INFO] 已删除失败需求记录 ID: {requirement_id}")
        except Exception as cleanup_error:
            db.rollback()
            print(f"[ERROR] 删除失败需求记录出错: {cleanup_error}")


def process_requirement_background(
    requirement_id: int,
    user_id: int,
    loop: Optional[asyncio.AbstractEventLoop] = None
):
    """后台处理需求文档（在线程池运行，避免阻塞事件循环）"""
    db = SessionLocal()
    requirement_file_path = None
    try:
        requirement = db.query(Requirement).filter(Requirement.id == requirement_id).first()
        if not requirement:
            return
        requirement_file_path = requirement.file_path

        # 更新状态为处理中
        requirement.status = RequirementStatus.PROCESSING
        db.commit()

        print(f"[INFO] 开始处理需求文档 ID: {requirement_id}")

        # 解析文档
        print(f"[INFO] 解析文档: {requirement.file_path}")
        text = DocumentParser.parse(requirement.file_path, requirement.file_type.value)
        if not text:
            raise ValueError("文档解析失败，内容为空")

        quality = DocumentParser.evaluate_quality(text)
        print(
            "[INFO] 文档解析成功，"
            f"文本长度 {len(text)}，有效字符 {quality['meaningful_chars']}, "
            f"非空行占比 {quality['non_empty_ratio']:.2%}"
        )

        if quality["meaningful_chars"] < settings.MIN_REQUIREMENT_CHARACTERS:
            raise ValueError(
                "文档有效字符过少，请确认是否上传了正确的需求内容"
            )
        if quality["non_empty_ratio"] < settings.MIN_NON_EMPTY_LINE_RATIO:
            raise ValueError(
                "文档空行占比过高，可能存在格式错误，请清理后重新上传"
            )

        chunks = document_embedding_service.split_text(text)
        try:
            vector_count = document_embedding_service.process_and_store(requirement_id, chunks)
            if vector_count:
                print(f"[INFO] 文档向量化完成，写入 {vector_count} 条向量")
            else:
                print("[INFO] 文档切分结果为空或未配置硅基流动 API Key，跳过向量入库")
        except Exception as vector_error:
            raise RuntimeError(f"文档向量化失败: {vector_error}") from vector_error

        ai_context = document_embedding_service.build_ai_context(chunks)
        if not ai_context:
            ai_context = text[: settings.TEST_POINT_MAX_INPUT_CHARS]
            print(
                "[WARNING] 无法基于切分构建上下文，直接截取原文作为模型输入，可能覆盖不完整"
            )

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
            try:
                test_points_data = ai_service.extract_test_points(
                    ai_context,
                    allow_fallback=False,
                )
            except Exception as ai_error:
                raise RuntimeError(f"AI 提取测试点失败: {ai_error}") from ai_error
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
        _run_async_notification(
            loop,
            manager.notify_test_point_generated(user_id, requirement_id, len(test_points_data)),
            "发送测试点生成通知失败"
        )

    except Exception as e:
        db.rollback()
        print(f"[ERROR] 处理需求失败 ID: {requirement_id}, 错误: {str(e)}")
        cleanup_failed_requirement(
            requirement_id,
            requirement_file_path,
            db,
            remove_requirement=True,
        )
        import traceback
        traceback.print_exc()
    finally:
        db.close()


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
    if file_size > settings.MAX_UPLOAD_SIZE:
        os.remove(file_path)
        max_mb = settings.MAX_UPLOAD_SIZE // (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制（>{max_mb}MB），请压缩或拆分后再上传",
        )
    
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
    loop = asyncio.get_running_loop()
    background_tasks.add_task(
        process_requirement_background,
        requirement.id,
        current_user.id,
        loop
    )
    
    return requirement


@router.get("/", response_model=List[RequirementWithStats])
def read_requirements(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search by title or file name"),
    file_category: Optional[str] = Query(None, description="Filter by file category: word/excel/pdf (comma separated for multi-select)"),
    statuses: Optional[str] = Query(None, description="Filter by statuses, comma separated"),
    start_date: Optional[datetime] = Query(None, description="Filter by created_at start time"),
    end_date: Optional[datetime] = Query(None, description="Filter by created_at end time"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取需求列表"""
    query = db.query(Requirement).filter(Requirement.user_id == current_user.id)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Requirement.title.ilike(search_pattern),
                Requirement.file_name.ilike(search_pattern),
            )
        )

    if file_category:
        selected_categories = [c.strip().lower() for c in file_category.split(",") if c.strip()]
        file_category_mapping = {
            "word": [FileType.DOCX],
            "excel": [FileType.XLS, FileType.XLSX],
            "pdf": [FileType.PDF],
        }
        allowed_types = []
        for category in selected_categories:
            allowed_types.extend(file_category_mapping.get(category, []))
        if allowed_types:
            query = query.filter(Requirement.file_type.in_(allowed_types))

    if statuses:
        selected_statuses = {
            status.strip().lower()
            for status in statuses.split(",")
            if status.strip()
        }
        valid_statuses = [status for status in RequirementStatus if status.value in selected_statuses]
        if valid_statuses:
            query = query.filter(Requirement.status.in_(valid_statuses))

    if start_date:
        query = query.filter(Requirement.created_at >= start_date)

    if end_date:
        query = query.filter(Requirement.created_at <= end_date)

    requirements = (
        query.order_by(Requirement.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
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

