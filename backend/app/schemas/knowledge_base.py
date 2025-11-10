"""
知识库 Schema
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ 知识库文档 Schema ============

class KnowledgeDocumentBase(BaseModel):
    """知识库文档基础 Schema"""
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[str] = None


class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    """创建知识库文档"""
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    collection_name: str = "knowledge_base"


class KnowledgeDocumentUpdate(BaseModel):
    """更新知识库文档"""
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    status: Optional[str] = None


class KnowledgeDocumentInDB(KnowledgeDocumentBase):
    """数据库中的知识库文档"""
    id: int
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_path: Optional[str] = None
    collection_name: str
    chunk_count: int
    is_vectorized: bool
    status: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KnowledgeDocument(KnowledgeDocumentInDB):
    """知识库文档"""
    pass


class KnowledgeDocumentList(BaseModel):
    """知识库文档列表"""
    total: int
    items: List[KnowledgeDocument]


# ============ 问答记录 Schema ============

class QARecordBase(BaseModel):
    """问答记录基础 Schema"""
    question: str
    answer: str


class QARecordCreate(BaseModel):
    """创建问答记录"""
    question: str
    collection_name: str = "knowledge_base"
    document_id: Optional[int] = None


class QARecordUpdate(BaseModel):
    """更新问答记录"""
    is_helpful: Optional[bool] = None
    feedback: Optional[str] = None
    rating: Optional[int] = None


class QARecordInDB(QARecordBase):
    """数据库中的问答记录"""
    id: int
    document_id: Optional[int] = None
    collection_name: str
    source_count: int
    sources: Optional[str] = None
    is_helpful: Optional[bool] = None
    feedback: Optional[str] = None
    rating: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class QARecord(QARecordInDB):
    """问答记录"""
    pass


class QARecordWithSources(QARecord):
    """带来源的问答记录"""
    sources_parsed: Optional[List[Dict[str, Any]]] = None


class QARecordList(BaseModel):
    """问答记录列表"""
    total: int
    items: List[QARecord]


# ============ API 请求/响应 Schema ============

class DocumentUploadRequest(BaseModel):
    """文档上传请求"""
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[str] = None
    collection_name: str = "knowledge_base"


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    success: bool
    document_id: Optional[int] = None
    total_chunks: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None


class ChatMessage(BaseModel):
    """对话消息"""
    role: str  # "user" 或 "assistant"
    content: str


class QuestionRequest(BaseModel):
    """问答请求 (支持对话历史)"""
    question: str
    collection_name: str = "knowledge_base"
    top_k: int = 5
    return_source: bool = True
    chat_history: Optional[List[ChatMessage]] = None  # 对话历史


class QuestionResponse(BaseModel):
    """问答响应"""
    success: bool
    question: str
    answer: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    qa_record_id: Optional[int] = None
    error: Optional[str] = None


class SimilarSearchRequest(BaseModel):
    """相似搜索请求"""
    query: str
    collection_name: str = "knowledge_base"
    top_k: int = 5


class SimilarSearchResponse(BaseModel):
    """相似搜索响应"""
    success: bool
    query: str
    results: List[Dict[str, Any]]
    error: Optional[str] = None


class FeedbackRequest(BaseModel):
    """反馈请求"""
    qa_record_id: int
    is_helpful: Optional[bool] = None
    feedback: Optional[str] = None
    rating: Optional[int] = None


class FeedbackResponse(BaseModel):
    """反馈响应"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class CollectionInfo(BaseModel):
    """集合信息"""
    name: str
    document_count: int
    total_chunks: int


class CollectionListResponse(BaseModel):
    """集合列表响应"""
    success: bool
    collections: List[CollectionInfo]
    error: Optional[str] = None

