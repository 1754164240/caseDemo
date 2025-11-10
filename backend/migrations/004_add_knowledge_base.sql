-- 添加知识库相关表

-- 1. 创建知识库文档表
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    file_name VARCHAR(500),
    file_type VARCHAR(50),
    file_size INTEGER,
    file_path VARCHAR(1000),
    category VARCHAR(100),
    tags VARCHAR(500),
    collection_name VARCHAR(200) DEFAULT 'knowledge_base',
    chunk_count INTEGER DEFAULT 0,
    is_vectorized BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'active',
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- 添加注释
COMMENT ON TABLE knowledge_documents IS '知识库文档表';
COMMENT ON COLUMN knowledge_documents.title IS '文档标题';
COMMENT ON COLUMN knowledge_documents.content IS '文档内容';
COMMENT ON COLUMN knowledge_documents.file_name IS '原始文件名';
COMMENT ON COLUMN knowledge_documents.file_type IS '文件类型';
COMMENT ON COLUMN knowledge_documents.file_size IS '文件大小(字节)';
COMMENT ON COLUMN knowledge_documents.file_path IS '文件路径';
COMMENT ON COLUMN knowledge_documents.category IS '文档分类';
COMMENT ON COLUMN knowledge_documents.tags IS '标签(逗号分隔)';
COMMENT ON COLUMN knowledge_documents.collection_name IS 'Milvus 集合名称';
COMMENT ON COLUMN knowledge_documents.chunk_count IS '文本块数量';
COMMENT ON COLUMN knowledge_documents.is_vectorized IS '是否已向量化';
COMMENT ON COLUMN knowledge_documents.status IS '状态: active/archived/deleted';
COMMENT ON COLUMN knowledge_documents.created_by IS '创建者ID';
COMMENT ON COLUMN knowledge_documents.created_at IS '创建时间';
COMMENT ON COLUMN knowledge_documents.updated_at IS '更新时间';

-- 创建索引
CREATE INDEX idx_knowledge_documents_category ON knowledge_documents(category);
CREATE INDEX idx_knowledge_documents_status ON knowledge_documents(status);
CREATE INDEX idx_knowledge_documents_created_by ON knowledge_documents(created_by);
CREATE INDEX idx_knowledge_documents_created_at ON knowledge_documents(created_at DESC);


-- 2. 创建问答记录表
CREATE TABLE IF NOT EXISTS qa_records (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    document_id INTEGER REFERENCES knowledge_documents(id),
    collection_name VARCHAR(200) DEFAULT 'knowledge_base',
    source_count INTEGER DEFAULT 0,
    sources TEXT,
    is_helpful BOOLEAN,
    feedback TEXT,
    rating INTEGER,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 添加注释
COMMENT ON TABLE qa_records IS '问答记录表';
COMMENT ON COLUMN qa_records.question IS '用户问题';
COMMENT ON COLUMN qa_records.answer IS 'AI 回答';
COMMENT ON COLUMN qa_records.document_id IS '关联文档ID';
COMMENT ON COLUMN qa_records.collection_name IS '使用的集合名称';
COMMENT ON COLUMN qa_records.source_count IS '引用的来源数量';
COMMENT ON COLUMN qa_records.sources IS '来源文档(JSON格式)';
COMMENT ON COLUMN qa_records.is_helpful IS '是否有帮助';
COMMENT ON COLUMN qa_records.feedback IS '用户反馈';
COMMENT ON COLUMN qa_records.rating IS '评分(1-5)';
COMMENT ON COLUMN qa_records.created_by IS '提问者ID';
COMMENT ON COLUMN qa_records.created_at IS '创建时间';

-- 创建索引
CREATE INDEX idx_qa_records_document_id ON qa_records(document_id);
CREATE INDEX idx_qa_records_created_by ON qa_records(created_by);
CREATE INDEX idx_qa_records_created_at ON qa_records(created_at DESC);
CREATE INDEX idx_qa_records_is_helpful ON qa_records(is_helpful);

