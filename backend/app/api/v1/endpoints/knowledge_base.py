"""
知识库 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import os
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.knowledge_base import KnowledgeDocument, QARecord
from app.schemas.knowledge_base import (
    KnowledgeDocument as KnowledgeDocumentSchema,
    KnowledgeDocumentCreate,
    KnowledgeDocumentUpdate,
    KnowledgeDocumentList,
    QARecord as QARecordSchema,
    QARecordList,
    DocumentUploadRequest,
    DocumentUploadResponse,
    QuestionRequest,
    QuestionResponse,
    SimilarSearchRequest,
    SimilarSearchResponse,
    FeedbackRequest,
    FeedbackResponse,
    CollectionListResponse,
    CollectionInfo,
)
from app.services.rag_service import RAGService
from app.api.deps import get_current_active_user
from app.core.config import settings


router = APIRouter()


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    title: str = Form(...),
    content: str = Form(...),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    collection_name: str = Form("knowledge_base"),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    上传文档到知识库
    """
    try:
        # 如果有文件上传，保存文件
        file_path = None
        file_name = None
        file_type = None
        file_size = None
        
        if file:
            # 创建上传目录
            upload_dir = os.path.join(settings.UPLOAD_DIR, "knowledge_base")
            os.makedirs(upload_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = file.filename
            file_ext = os.path.splitext(file_name)[1]
            safe_filename = f"{timestamp}_{file_name}"
            file_path = os.path.join(upload_dir, safe_filename)
            
            # 保存文件
            with open(file_path, "wb") as f:
                content_bytes = await file.read()
                f.write(content_bytes)
            
            file_type = file.content_type
            file_size = len(content_bytes)
        
        # 创建文档记录
        document = KnowledgeDocument(
            title=title,
            content=content,
            category=category,
            tags=tags,
            collection_name=collection_name,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            created_by=current_user.id,
            is_vectorized=False,
            chunk_count=0
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # 向量化文档
        rag_service = RAGService(db)
        result = rag_service.add_documents(
            documents=[content],
            metadatas=[{
                "document_id": document.id,
                "title": title,
                "category": category or "",
                "tags": tags or "",
            }],
            collection_name=collection_name
        )
        
        if result["success"]:
            # 更新文档状态
            document.is_vectorized = True
            document.chunk_count = result["total_chunks"]
            db.commit()
            
            return DocumentUploadResponse(
                success=True,
                document_id=document.id,
                total_chunks=result["total_chunks"],
                message="文档上传并向量化成功"
            )
        else:
            return DocumentUploadResponse(
                success=False,
                error=result.get("error", "向量化失败")
            )
            
    except Exception as e:
        print(f"[ERROR] 上传文档失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=KnowledgeDocumentList)
def get_documents(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    status: str = "active",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取知识库文档列表
    """
    query = db.query(KnowledgeDocument).filter(KnowledgeDocument.status == status)
    
    if category:
        query = query.filter(KnowledgeDocument.category == category)
    
    total = query.count()
    documents = query.order_by(KnowledgeDocument.created_at.desc()).offset(skip).limit(limit).all()
    
    return KnowledgeDocumentList(
        total=total,
        items=documents
    )


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentSchema)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取文档详情
    """
    document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return document


@router.put("/documents/{document_id}", response_model=KnowledgeDocumentSchema)
def update_document(
    document_id: int,
    document_update: KnowledgeDocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新文档
    """
    document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 更新字段
    update_data = document_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)
    
    db.commit()
    db.refresh(document)
    
    return document


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除文档
    """
    document = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 软删除
    document.status = "deleted"
    db.commit()
    
    return {"success": True, "message": "文档已删除"}


@router.post("/query", response_model=QuestionResponse)
def query_knowledge_base(
    request: QuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    查询知识库 (支持对话历史)
    """
    try:
        # 转换对话历史为字典格式
        chat_history = None
        if request.chat_history:
            chat_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.chat_history
            ]

        # 使用 RAG 服务查询
        rag_service = RAGService(db)
        result = rag_service.query(
            question=request.question,
            collection_name=request.collection_name,
            top_k=request.top_k,
            return_source=request.return_source,
            chat_history=chat_history
        )
        
        if not result["success"]:
            return QuestionResponse(
                success=False,
                question=request.question,
                error=result.get("error", "查询失败")
            )
        
        # 保存问答记录
        qa_record = QARecord(
            question=request.question,
            answer=result["answer"],
            collection_name=request.collection_name,
            source_count=len(result.get("sources", [])),
            sources=json.dumps(result.get("sources", []), ensure_ascii=False),
            created_by=current_user.id
        )
        
        db.add(qa_record)
        db.commit()
        db.refresh(qa_record)
        
        return QuestionResponse(
            success=True,
            question=request.question,
            answer=result["answer"],
            sources=result.get("sources", []),
            qa_record_id=qa_record.id
        )
        
    except Exception as e:
        print(f"[ERROR] 查询知识库失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def query_knowledge_base_stream(
    request: QuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    流式查询知识库 (Server-Sent Events, 支持对话历史)
    """
    async def event_generator():
        try:
            # 转换对话历史为字典格式
            chat_history = None
            if request.chat_history:
                chat_history = [
                    {"role": msg.role, "content": msg.content}
                    for msg in request.chat_history
                ]

            # 使用 RAG 服务流式查询
            rag_service = RAGService(db)

            # 获取流式响应生成器
            stream_gen = rag_service.query(
                question=request.question,
                collection_name=request.collection_name,
                top_k=request.top_k,
                return_source=request.return_source,
                stream=True,
                chat_history=chat_history
            )

            # 用于保存完整答案
            full_answer = ""
            sources = []

            # 流式发送数据
            for chunk in stream_gen:
                yield chunk

                # 解析数据以保存记录
                if chunk.startswith("data: "):
                    data_str = chunk[6:].strip()
                    if data_str:
                        try:
                            data = json.loads(data_str)
                            if data.get("type") == "sources":
                                sources = data.get("sources", [])
                            elif data.get("type") == "done":
                                full_answer = data.get("answer", "")
                        except:
                            pass

            # 保存问答记录
            if full_answer:
                qa_record = QARecord(
                    question=request.question,
                    answer=full_answer,
                    collection_name=request.collection_name,
                    source_count=len(sources),
                    sources=json.dumps(sources, ensure_ascii=False),
                    created_by=current_user.id
                )

                db.add(qa_record)
                db.commit()
                db.refresh(qa_record)

                # 发送 QA 记录 ID
                yield f"data: {json.dumps({'type': 'qa_record_id', 'qa_record_id': qa_record.id}, ensure_ascii=False)}\n\n"

        except Exception as e:
            print(f"[ERROR] 流式查询失败: {str(e)}")
            import traceback
            traceback.print_exc()
            error_data = json.dumps({"type": "error", "error": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/search", response_model=SimilarSearchResponse)
def search_similar_documents(
    request: SimilarSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    搜索相似文档
    """
    try:
        rag_service = RAGService(db)
        results = rag_service.search_similar(
            query=request.query,
            collection_name=request.collection_name,
            top_k=request.top_k
        )
        
        return SimilarSearchResponse(
            success=True,
            query=request.query,
            results=results
        )
        
    except Exception as e:
        print(f"[ERROR] 搜索失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/qa-records", response_model=QARecordList)
def get_qa_records(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取问答记录列表
    """
    total = db.query(QARecord).count()
    records = db.query(QARecord).order_by(QARecord.created_at.desc()).offset(skip).limit(limit).all()
    
    return QARecordList(
        total=total,
        items=records
    )


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    提交问答反馈
    """
    qa_record = db.query(QARecord).filter(QARecord.id == request.qa_record_id).first()
    if not qa_record:
        raise HTTPException(status_code=404, detail="问答记录不存在")
    
    # 更新反馈
    if request.is_helpful is not None:
        qa_record.is_helpful = request.is_helpful
    if request.feedback:
        qa_record.feedback = request.feedback
    if request.rating is not None:
        qa_record.rating = request.rating
    
    db.commit()
    
    return FeedbackResponse(
        success=True,
        message="反馈提交成功"
    )

