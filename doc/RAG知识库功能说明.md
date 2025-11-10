# RAG 知识库功能说明

## 功能概述

基于 LangChain 和 Milvus 实现的 RAG (Retrieval-Augmented Generation) 知识库问答系统,支持文档上传、向量化存储和智能问答。

## 技术架构

### 核心技术栈

- **LangChain**: LLM 应用开发框架
- **OpenAI Embeddings**: 文本向量化
- **Milvus**: 向量数据库
- **FastAPI**: 后端 API 框架
- **React + Ant Design**: 前端界面

### RAG 工作流程

```
1. 文档上传
   ↓
2. 文本分割 (RecursiveCharacterTextSplitter)
   - chunk_size: 1000
   - chunk_overlap: 200
   ↓
3. 向量化 (OpenAI Embeddings)
   - 生成 1536 维向量
   ↓
4. 存储到 Milvus
   - collection: knowledge_base
   ↓
5. 用户提问
   ↓
6. 问题向量化
   ↓
7. 向量相似度搜索 (Top-K)
   ↓
8. 检索相关文档片段
   ↓
9. 构建 Prompt (问题 + 上下文)
   ↓
10. LLM 生成回答
   ↓
11. 返回答案 + 来源
```

## 后端实现

### 1. RAG 服务 (`backend/app/services/rag_service.py`)

#### 核心功能

**文档添加**:
```python
def add_documents(
    documents: List[str], 
    metadatas: Optional[List[Dict[str, Any]]] = None,
    collection_name: str = "knowledge_base"
) -> Dict[str, Any]
```

**知识库查询**:
```python
def query(
    question: str, 
    collection_name: str = "knowledge_base",
    top_k: int = 5,
    return_source: bool = True
) -> Dict[str, Any]
```

**相似文档搜索**:
```python
def search_similar(
    query: str, 
    collection_name: str = "knowledge_base",
    top_k: int = 5
) -> List[Dict[str, Any]]
```

#### 文本分割策略

```python
RecursiveCharacterTextSplitter(
    chunk_size=1000,        # 每个文本块 1000 字符
    chunk_overlap=200,      # 重叠 200 字符
    length_function=len,
    separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
)
```

#### Prompt 模板

```python
system_prompt = """你是一个专业的保险行业知识助手。请根据以下上下文信息回答用户的问题。

上下文信息:
{context}

回答要求:
1. 基于上下文信息提供准确、专业的回答
2. 如果上下文中没有相关信息，请明确说明"根据现有知识库，我无法回答这个问题"
3. 回答要简洁明了，重点突出
4. 如果涉及专业术语，请适当解释
5. 可以引用上下文中的具体内容来支持你的回答

用户问题: {question}

请提供详细的回答:"""
```

### 2. 数据模型

#### KnowledgeDocument (知识库文档)

```python
class KnowledgeDocument(Base):
    id: int                          # 主键
    title: str                       # 文档标题
    content: str                     # 文档内容
    file_name: str                   # 原始文件名
    file_type: str                   # 文件类型
    file_size: int                   # 文件大小
    file_path: str                   # 文件路径
    category: str                    # 文档分类
    tags: str                        # 标签(逗号分隔)
    collection_name: str             # Milvus 集合名称
    chunk_count: int                 # 文本块数量
    is_vectorized: bool              # 是否已向量化
    status: str                      # 状态
    created_by: int                  # 创建者ID
    created_at: datetime             # 创建时间
    updated_at: datetime             # 更新时间
```

#### QARecord (问答记录)

```python
class QARecord(Base):
    id: int                          # 主键
    question: str                    # 用户问题
    answer: str                      # AI 回答
    document_id: int                 # 关联文档ID
    collection_name: str             # 使用的集合名称
    source_count: int                # 引用的来源数量
    sources: str                     # 来源文档(JSON格式)
    is_helpful: bool                 # 是否有帮助
    feedback: str                    # 用户反馈
    rating: int                      # 评分(1-5)
    created_by: int                  # 提问者ID
    created_at: datetime             # 创建时间
```

### 3. API 端点

#### 文档管理

- `POST /api/v1/knowledge-base/documents/upload` - 上传文档
- `GET /api/v1/knowledge-base/documents` - 获取文档列表
- `GET /api/v1/knowledge-base/documents/{id}` - 获取文档详情
- `PUT /api/v1/knowledge-base/documents/{id}` - 更新文档
- `DELETE /api/v1/knowledge-base/documents/{id}` - 删除文档

#### 问答功能

- `POST /api/v1/knowledge-base/query` - 查询知识库
- `POST /api/v1/knowledge-base/search` - 搜索相似文档
- `GET /api/v1/knowledge-base/qa-records` - 获取问答记录
- `POST /api/v1/knowledge-base/feedback` - 提交反馈

## 前端实现

### 页面布局

```
┌─────────────────────────────────────────────────────────┐
│ 知识问答                                                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────┐  ┌──────────────────────┐  │
│  │ 提问区域                │  │ 知识库文档列表        │  │
│  │                        │  │                      │  │
│  │ [文本输入框]            │  │ • 文档1 (10块)       │  │
│  │                        │  │ • 文档2 (15块)       │  │
│  │ [提问按钮]              │  │ • 文档3 (8块)        │  │
│  │                        │  │                      │  │
│  ├────────────────────────┤  └──────────────────────┘  │
│  │ 回答显示区域            │                            │
│  │                        │                            │
│  │ [AI 回答内容]           │                            │
│  │                        │                            │
│  │ [有帮助] [没帮助] [复制] │                            │
│  │                        │                            │
│  ├────────────────────────┤                            │
│  │ 参考来源                │                            │
│  │                        │                            │
│  │ • 来源1: [文档片段]     │                            │
│  │ • 来源2: [文档片段]     │                            │
│  │ • 来源3: [文档片段]     │                            │
│  └────────────────────────┘                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 核心功能

#### 1. 文档上传

```typescript
const handleUploadDocument = async (values: any) => {
  const formData = new FormData()
  formData.append('title', values.title)
  formData.append('content', values.content)
  formData.append('category', values.category)
  formData.append('tags', values.tags)
  formData.append('collection_name', 'knowledge_base')
  
  const response = await api.post('/knowledge-base/documents/upload', formData)
}
```

#### 2. 智能问答

```typescript
const handleAsk = async () => {
  const response = await api.post('/knowledge-base/query', {
    question: question.trim(),
    collection_name: 'knowledge_base',
    top_k: 5,
    return_source: true,
  })
  
  setCurrentAnswer({
    question: response.data.question,
    answer: response.data.answer,
    sources: response.data.sources,
    qa_record_id: response.data.qa_record_id,
  })
}
```

#### 3. 反馈提交

```typescript
const handleFeedback = async (isHelpful: boolean) => {
  await api.post('/knowledge-base/feedback', {
    qa_record_id: currentAnswer.qa_record_id,
    is_helpful: isHelpful,
  })
}
```

## 使用指南

### 1. 上传文档到知识库

1. 点击 "上传文档" 按钮
2. 填写文档信息:
   - 文档标题 (必填)
   - 文档内容 (必填)
   - 分类 (可选): 例如 "契约"、"保全"、"理赔"
   - 标签 (可选): 多个标签用逗号分隔
3. 点击 "确定" 上传
4. 系统自动:
   - 分割文档为多个文本块
   - 向量化每个文本块
   - 存储到 Milvus 向量数据库

### 2. 提问

1. 在输入框中输入问题
2. 点击 "提问" 按钮或按 Ctrl+Enter
3. AI 会:
   - 将问题向量化
   - 搜索最相关的文档片段 (Top-5)
   - 基于检索到的内容生成回答
   - 返回答案和参考来源

### 3. 查看来源

- 每个回答都会显示参考来源
- 来源包含:
  - 来源序号
  - 文档标题
  - 文档分类
  - 文档片段内容

### 4. 提交反馈

- 点击 "有帮助" 或 "没帮助" 按钮
- 反馈会被记录,用于改进系统

### 5. 查看历史记录

- 点击 "历史记录" 按钮
- 查看所有问答历史
- 包含问题、答案、时间、反馈状态

## 配置说明

### Milvus 配置

在系统配置页面配置 Milvus 连接:

```
URI: http://localhost:19530
User: (可选)
Password: (可选)
Token: (可选)
Database: default
Collection: knowledge_base
```

### OpenAI 配置

在系统配置页面配置 OpenAI API:

```
API Key: your_api_key
API Base: https://api.openai.com/v1
Model: gpt-4
```

## 最佳实践

### 1. 文档准备

- **结构化内容**: 文档内容应该结构清晰,段落分明
- **适当长度**: 单个文档建议 1000-10000 字
- **准确分类**: 为文档添加准确的分类和标签
- **避免重复**: 不要上传重复或高度相似的文档

### 2. 提问技巧

- **明确具体**: 问题要明确具体,避免过于宽泛
- **关键词**: 包含关键词有助于检索相关内容
- **上下文**: 如果需要,提供必要的上下文信息
- **分步提问**: 复杂问题可以分步提问

### 3. 知识库维护

- **定期更新**: 及时更新过时的文档
- **质量优先**: 保证文档内容的准确性和专业性
- **合理分类**: 使用统一的分类体系
- **标签管理**: 使用一致的标签命名规范

## 性能优化

### 1. 文本分割

- `chunk_size=1000`: 平衡检索精度和上下文完整性
- `chunk_overlap=200`: 避免重要信息在分割边界丢失

### 2. 向量检索

- `top_k=5`: 检索 5 个最相关的文档片段
- 可根据实际情况调整 (3-10)

### 3. LLM 参数

- `temperature=0.3`: 降低随机性,提高答案准确性
- 可根据需要调整 (0.0-1.0)

## 故障排查

### 问题 1: 上传文档失败

**可能原因**:
- Milvus 未启动或连接失败
- OpenAI API Key 未配置或无效

**解决方案**:
1. 检查 Milvus 服务状态: `docker ps`
2. 检查 OpenAI API Key 配置
3. 查看后端日志

### 问题 2: 查询无结果

**可能原因**:
- 知识库为空
- 问题与知识库内容不相关
- 向量化失败

**解决方案**:
1. 确认已上传文档
2. 检查文档是否已向量化 (`is_vectorized=true`)
3. 尝试更换问题关键词

### 问题 3: 回答不准确

**可能原因**:
- 检索到的文档片段不相关
- 文档内容质量问题
- Prompt 需要优化

**解决方案**:
1. 查看参考来源,确认检索质量
2. 优化文档内容和结构
3. 调整 `top_k` 参数
4. 优化 Prompt 模板

## 未来扩展

1. **多模态支持**: 支持图片、表格等多模态内容
2. **文档解析**: 自动解析 PDF、Word、Excel 等文件
3. **知识图谱**: 构建知识图谱增强检索
4. **对话记忆**: 支持多轮对话上下文
5. **权限管理**: 文档级别的访问权限控制
6. **批量导入**: 支持批量导入文档
7. **智能推荐**: 基于历史问答推荐相关问题
8. **导出功能**: 导出问答记录和知识库

## 相关文件

### 后端

- `backend/app/services/rag_service.py` - RAG 服务
- `backend/app/models/knowledge_base.py` - 数据模型
- `backend/app/schemas/knowledge_base.py` - Schema 定义
- `backend/app/api/v1/endpoints/knowledge_base.py` - API 端点
- `backend/migrations/004_add_knowledge_base.sql` - 数据库迁移
- `backend/run_knowledge_base_migration.py` - 迁移脚本

### 前端

- `frontend/src/pages/KnowledgeBase.tsx` - 知识库页面
- `frontend/src/App.tsx` - 路由配置
- `frontend/src/components/Layout.tsx` - 布局组件

### 文档

- `doc/RAG知识库功能说明.md` - 本文档

