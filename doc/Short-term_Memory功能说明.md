# LangChain Short-term Memory 功能说明

## ✅ 功能已实现!

### 功能描述
实现了 LangChain 的 Short-term Memory (短期记忆) 功能,支持多轮对话上下文理解。AI 能够记住之前的对话内容,理解代词引用和上下文关系。

### 核心特性

#### 1. **对话历史管理** ✅
- 前端自动维护对话历史
- 每次提问时发送完整对话历史
- 支持无限轮对话

#### 2. **上下文理解** ✅
- AI 能理解代词引用 (如 "它"、"这个"、"那个")
- AI 能理解上下文关系 (如 "第一种"、"刚才提到的")
- AI 能基于历史对话提供连贯回答

#### 3. **RAG + Memory** ✅
- 结合知识库检索和对话历史
- 优先使用知识库内容,辅以对话历史理解
- 即使知识库为空,也能基于对话历史回答

---

## 实现原理

### 1. LangChain 消息格式

使用 LangChain 的标准消息类型:

```python
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# 用户消息
HumanMessage(content="什么是保险?")

# AI 消息
AIMessage(content="保险是一种风险管理工具...")
```

### 2. Prompt 模板支持对话历史

使用 `MessagesPlaceholder` 插入对话历史:

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 有对话历史的 Prompt
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的保险行业知识助手。
    
上下文信息:
{context}

请根据上下文信息和对话历史回答用户的问题。"""),
    MessagesPlaceholder(variable_name="chat_history"),  # 插入对话历史
    ("human", "{question}"),
])

# 格式化消息
messages = qa_prompt.format_messages(
    context=context,
    chat_history=history_messages,  # 传入对话历史
    question=question
)
```

### 3. 对话历史解析

将前端发送的对话历史转换为 LangChain 消息:

```python
def _parse_chat_history(self, chat_history: Optional[List[Dict[str, str]]]) -> List[BaseMessage]:
    """
    解析对话历史为 LangChain 消息格式
    
    Args:
        chat_history: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    
    Returns:
        [HumanMessage(...), AIMessage(...), ...]
    """
    if not chat_history:
        return []
    
    messages = []
    for msg in chat_history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    
    return messages
```

---

## 使用示例

### 场景 1: 代词引用理解

```
用户: 什么是保险?
AI: 保险是一种风险管理工具,通过缴纳保费来转移风险...

用户: 它有哪些类型?  ← "它" 指代 "保险"
AI: 保险主要有以下几种类型:
    1. 人寿保险
    2. 财产保险
    3. 健康保险
    ...
```

**关键点**: AI 能理解 "它" 指的是上一轮对话中的 "保险"

---

### 场景 2: 上下文关系理解

```
用户: 投保流程是什么?
AI: 投保流程包括以下步骤:
    1. 填写投保申请书
    2. 提交健康告知
    3. 核保审核
    4. 缴纳保费
    5. 生成保单

用户: 第二步需要注意什么?  ← "第二步" 指代 "提交健康告知"
AI: 提交健康告知时需要注意:
    1. 如实告知健康状况
    2. 不得隐瞒既往病史
    ...
```

**关键点**: AI 能理解 "第二步" 指的是上一轮回答中的 "提交健康告知"

---

### 场景 3: 多轮追问

```
用户: 保单变更需要多长时间?
AI: 保单变更需要 3-5 个工作日。

用户: 如果加急呢?  ← 继续追问
AI: 如果需要加急处理,可以申请特殊通道,通常 1-2 个工作日即可完成...

用户: 需要额外费用吗?  ← 继续追问
AI: 加急服务通常需要支付一定的加急费用,具体金额根据...
```

**关键点**: AI 能理解每一轮问题都是基于之前的对话内容

---

## 技术实现

### 后端实现

#### 1. RAG 服务 (`backend/app/services/rag_service.py`)

**添加对话历史解析方法**:
```python
def _parse_chat_history(self, chat_history: Optional[List[Dict[str, str]]]) -> List[BaseMessage]:
    """解析对话历史为 LangChain 消息格式"""
    if not chat_history:
        return []
    
    messages = []
    for msg in chat_history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    
    return messages
```

**修改 query 方法支持对话历史**:
```python
def query(
    self,
    question: str,
    collection_name: str = "knowledge_base",
    top_k: int = 5,
    return_source: bool = True,
    stream: bool = False,
    chat_history: Optional[List[Dict[str, str]]] = None  # 新增参数
) -> Dict[str, Any]:
    # 解析对话历史
    history_messages = self._parse_chat_history(chat_history)
    
    # 创建支持对话历史的 Prompt
    if history_messages:
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", "..."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ])
        messages = qa_prompt.format_messages(
            context=context,
            chat_history=history_messages,
            question=question
        )
    else:
        # 无对话历史的 Prompt
        ...
```

#### 2. API Schema (`backend/app/schemas/knowledge_base.py`)

**添加对话消息 Schema**:
```python
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
```

#### 3. API 接口 (`backend/app/api/v1/endpoints/knowledge_base.py`)

**修改查询接口传递对话历史**:
```python
@router.post("/query/stream")
async def query_knowledge_base_stream(
    request: QuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 转换对话历史为字典格式
    chat_history = None
    if request.chat_history:
        chat_history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.chat_history
        ]
    
    # 使用 RAG 服务流式查询
    rag_service = RAGService(db)
    stream_gen = rag_service.query(
        question=request.question,
        collection_name=request.collection_name,
        top_k=request.top_k,
        return_source=request.return_source,
        stream=True,
        chat_history=chat_history  # 传递对话历史
    )
```

---

### 前端实现

#### 修改知识问答页面 (`frontend/src/pages/KnowledgeBase.tsx`)

**发送对话历史**:
```typescript
const handleAsk = async () => {
  // 构建对话历史 (只发送最近的消息,不包括当前问题)
  const chatHistory = messages.map(msg => ({
    role: msg.type === 'user' ? 'user' : 'assistant',
    content: msg.content,
  }))

  const response = await fetch('/api/v1/knowledge-base/query/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      question: userQuestion,
      collection_name: 'knowledge_base',
      top_k: 5,
      return_source: true,
      chat_history: chatHistory,  // 发送对话历史
    }),
  })
}
```

---

## 测试方法

### 方法 1: 使用测试脚本

```bash
cd backend
python -m scripts.test_memory
```

**测试场景**:
1. 第 1 轮: "什么是保险?"
2. 第 2 轮: "它有哪些类型?" (引用 "保险")
3. 第 3 轮: "第一种类型的特点是什么?" (引用上一轮的回答)

**预期结果**:
- ✅ AI 能正确理解 "它" 指代 "保险"
- ✅ AI 能正确理解 "第一种类型" 指什么
- ✅ 回答连贯,符合上下文

---

### 方法 2: 浏览器测试

1. **访问知识问答页面**
   - http://localhost:5173
   - 登录 (admin / admin123)
   - 点击 "知识问答"

2. **测试多轮对话**
   ```
   第 1 轮: 什么是保险?
   第 2 轮: 它有哪些类型?
   第 3 轮: 第一种类型的特点是什么?
   ```

3. **观察效果**
   - ✅ AI 能理解代词引用
   - ✅ AI 能理解上下文关系
   - ✅ 回答连贯自然

---

## 对话历史管理策略

### 当前策略: 发送全部历史

**优点**:
- 实现简单
- 上下文完整

**缺点**:
- Token 消耗大
- 可能超出模型上下文长度限制

### 优化策略 (可选)

#### 1. **限制历史长度**
```typescript
// 只发送最近 N 轮对话
const MAX_HISTORY_ROUNDS = 5
const chatHistory = messages.slice(-MAX_HISTORY_ROUNDS * 2).map(msg => ({
  role: msg.type === 'user' ? 'user' : 'assistant',
  content: msg.content,
}))
```

#### 2. **使用 LangChain ConversationBufferWindowMemory**
```python
from langchain.memory import ConversationBufferWindowMemory

# 只保留最近 k 轮对话
memory = ConversationBufferWindowMemory(k=5)
```

#### 3. **使用 LangChain ConversationSummaryMemory**
```python
from langchain.memory import ConversationSummaryMemory

# 自动总结历史对话,减少 Token 消耗
memory = ConversationSummaryMemory(llm=llm)
```

---

## 相关文件

- ✅ `backend/app/services/rag_service.py` - RAG 服务支持对话历史
- ✅ `backend/app/schemas/knowledge_base.py` - 添加 ChatMessage Schema
- ✅ `backend/app/api/v1/endpoints/knowledge_base.py` - API 接口传递对话历史
- ✅ `frontend/src/pages/KnowledgeBase.tsx` - 前端发送对话历史
- ✅ `backend/scripts/test_memory.py` - 测试脚本
- ✅ `doc/Short-term_Memory功能说明.md` - 功能文档

---

## 下一步

1. **测试功能**: 运行 `python -m scripts.test_memory` 测试对话历史功能
2. **浏览器测试**: 在浏览器中测试多轮对话
3. **优化策略**: 根据需要实现对话历史长度限制或总结功能

所有功能已实现! 🎉 现在支持 Short-term Memory 多轮对话了! 🎊
