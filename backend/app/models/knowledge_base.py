"""
知识库模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class KnowledgeDocument(Base):
    """知识库文档表"""
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, comment="文档标题")
    content = Column(Text, nullable=False, comment="文档内容")
    file_name = Column(String(500), comment="原始文件名")
    file_type = Column(String(50), comment="文件类型")
    file_size = Column(Integer, comment="文件大小(字节)")
    file_path = Column(String(1000), comment="文件路径")
    
    # 分类和标签
    category = Column(String(100), comment="文档分类")
    tags = Column(String(500), comment="标签(逗号分隔)")
    
    # 向量化信息
    collection_name = Column(String(200), default="knowledge_base", comment="Milvus 集合名称")
    chunk_count = Column(Integer, default=0, comment="文本块数量")
    is_vectorized = Column(Boolean, default=False, comment="是否已向量化")
    
    # 状态
    status = Column(String(50), default="active", comment="状态: active/archived/deleted")
    
    # 创建者
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建者ID")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    
    # 关系
    creator = relationship("User", back_populates="knowledge_documents")
    qa_records = relationship("QARecord", back_populates="document", cascade="all, delete-orphan")


class QARecord(Base):
    """问答记录表"""
    __tablename__ = "qa_records"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False, comment="用户问题")
    answer = Column(Text, nullable=False, comment="AI 回答")
    
    # 关联文档
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"), nullable=True, comment="关联文档ID")
    
    # 检索信息
    collection_name = Column(String(200), default="knowledge_base", comment="使用的集合名称")
    source_count = Column(Integer, default=0, comment="引用的来源数量")
    sources = Column(Text, comment="来源文档(JSON格式)")
    
    # 反馈
    is_helpful = Column(Boolean, nullable=True, comment="是否有帮助")
    feedback = Column(Text, comment="用户反馈")
    rating = Column(Integer, comment="评分(1-5)")
    
    # 创建者
    created_by = Column(Integer, ForeignKey("users.id"), comment="提问者ID")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关系
    document = relationship("KnowledgeDocument", back_populates="qa_records")
    creator = relationship("User", back_populates="qa_records")

