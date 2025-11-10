# LangChain 流式输出功能说明

## 功能概述

实现了基于 LangChain 的流式输出功能,让 AI 回答像打字机一样逐字显示,提供更好的用户体验。

## 技术架构

### 1. 后端实现

#### 1.1 RAG 服务流式支持

**文件**: `backend/app/services/rag_service.py`

**核心方法**:

```python
def query(
    self, 
    question: str, 
    collection_name: str = "knowledge_base",
    top_k: int = 5,
    return_source: bool = True,
    stream: bool = False  # 新增参数
) -> Dict[str, Any]:
    """
    查询知识库
    
    Args:
        stream: 是否使用流式输出
    """
    # 如果使用流式输出
    if stream:
        return self._stream_response(messages, relevant_docs, question, return_source)
    
    # 非流式输出 (原有逻辑)
    ...
```

**流式响应生成器**:

```python
def _stream_response(self, messages, relevant_docs, question, return_source):
    """
    流式响应生成器
    
    Yields:
        SSE 格式的流式数据
    """
    import json
    
    # 1. 首先发送来源信息
    if return_source and relevant_docs:
        sources = [...]
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
    
    # 2. 流式生成回答
    full_answer = ""
    for chunk in self.llm.stream(messages):  # LangChain 流式 API
        if chunk.content:
            full_answer += chunk.content
            # 发送文本块
            yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
    
    # 3. 发送完成信号
    yield f"data: {json.dumps({'type': 'done', 'answer': full_answer})}\n\n"
```

**关键技术点**:
- 使用 `self.llm.stream(messages)` 获取 LangChain 流式输出
- 使用 Server-Sent Events (SSE) 格式发送数据
- 数据格式: `data: {JSON}\n\n`

#### 1.2 API 端点

**文件**: `backend/app/api/v1/endpoints/knowledge_base.py`

**新增端点**: `POST /api/v1/knowledge-base/query/stream`

```python
@router.post("/query/stream")
async def query_knowledge_base_stream(
    request: QuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    流式查询知识库 (Server-Sent Events)
    """
    async def event_generator():
        try:
            # 获取流式响应生成器
            rag_service = RAGService(db)
            stream_gen = rag_service.query(
                question=request.question,
                collection_name=request.collection_name,
                top_k=request.top_k,
                return_source=request.return_source,
                stream=True  # 启用流式
            )
            
            # 流式发送数据
            full_answer = ""
            sources = []
            
            for chunk in stream_gen:
                yield chunk
                
                # 解析数据以保存记录
                if chunk.startswith("data: "):
                    data = json.loads(chunk[6:].strip())
                    if data.get("type") == "sources":
                        sources = data.get("sources", [])
                    elif data.get("type") == "done":
                        full_answer = data.get("answer", "")
            
            # 保存问答记录
            if full_answer:
                qa_record = QARecord(...)
                db.add(qa_record)
                db.commit()
                
                # 发送 QA 记录 ID
                yield f"data: {json.dumps({'type': 'qa_record_id', 'qa_record_id': qa_record.id})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
```

**关键技术点**:
- 使用 `StreamingResponse` 返回流式数据
- `media_type="text/event-stream"` 指定 SSE 格式
- 设置正确的 HTTP 头防止缓存

### 2. 前端实现

#### 2.1 流式接收

**文件**: `frontend/src/pages/KnowledgeBase.tsx`

**核心逻辑**:

```typescript
const handleAsk = async () => {
  // 1. 添加用户消息
  const userMessage: Message = { ... }
  setMessages(prev => [...prev, userMessage])
  
  // 2. 创建 AI 消息占位符
  const assistantMessageId = `assistant-${Date.now()}`
  const assistantMessage: Message = {
    id: assistantMessageId,
    type: 'assistant',
    content: '',  // 初始为空
    timestamp: new Date(),
  }
  setMessages(prev => [...prev, assistantMessage])
  
  setLoading(true)
  setStreaming(true)
  
  try {
    // 3. 调用流式 API
    const response = await fetch('/api/v1/knowledge-base/query/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      },
      body: JSON.stringify({ ... }),
    })
    
    // 4. 读取流式响应
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    
    let buffer = ''
    let fullAnswer = ''
    let sources: Source[] = []
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      // 5. 解码数据
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      
      // 6. 处理每一行
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          
          if (data.type === 'sources') {
            // 接收来源信息
            sources = data.sources
          } else if (data.type === 'token') {
            // 接收文本块,逐字显示
            fullAnswer += data.content
            setMessages(prev => prev.map(msg =>
              msg.id === assistantMessageId
                ? { ...msg, content: fullAnswer, sources }
                : msg
            ))
          } else if (data.type === 'done') {
            // 完成
            fullAnswer = data.answer
          } else if (data.type === 'qa_record_id') {
            // 接收 QA 记录 ID
            qaRecordId = data.qa_record_id
          }
        }
      }
    }
  } finally {
    setLoading(false)
    setStreaming(false)
  }
}
```

**关键技术点**:
- 使用 `fetch` API 而不是 axios (axios 不支持流式响应)
- 使用 `ReadableStream` 读取流式数据
- 使用 `TextDecoder` 解码二进制数据
- 逐行解析 SSE 格式数据
- 实时更新消息内容

#### 2.2 打字机效果

**视觉效果**:

```tsx
<Paragraph>
  {msg.content}
  {/* 流式输出时显示光标 */}
  {msg.type === 'assistant' && streaming && idx === messages.length - 1 && (
    <span
      style={{
        display: 'inline-block',
        width: 8,
        height: 18,
        backgroundColor: '#52c41a',
        marginLeft: 4,
        animation: 'blink 1s infinite',
      }}
    />
  )}
</Paragraph>
```

**CSS 动画**:

```css
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
```

**效果**:
- 绿色光标闪烁
- 只在最后一条 AI 消息且正在流式输出时显示
- 1 秒闪烁一次

## 数据流程

### 完整流程图

```
用户输入问题
    ↓
前端: 添加用户消息到列表
    ↓
前端: 创建空的 AI 消息占位符
    ↓
前端: 调用流式 API
    ↓
后端: RAG 服务检索相关文档
    ↓
后端: 发送来源信息 (type: sources)
    ↓
前端: 接收来源,更新消息
    ↓
后端: LangChain 流式生成回答
    ↓
后端: 逐块发送文本 (type: token)
    ↓
前端: 逐字更新消息内容 (打字机效果)
    ↓
后端: 发送完成信号 (type: done)
    ↓
后端: 保存问答记录
    ↓
后端: 发送 QA 记录 ID (type: qa_record_id)
    ↓
前端: 接收 QA 记录 ID,更新消息
    ↓
前端: 停止流式状态,隐藏光标
```

### SSE 数据格式

#### 1. 来源信息
```
data: {"type": "sources", "sources": [...]}

```

#### 2. 文本块
```
data: {"type": "token", "content": "根据"}

data: {"type": "token", "content": "契约"}

data: {"type": "token", "content": "业务"}

...
```

#### 3. 完成信号
```
data: {"type": "done", "answer": "完整答案..."}

```

#### 4. QA 记录 ID
```
data: {"type": "qa_record_id", "qa_record_id": 123}

```

#### 5. 错误信息
```
data: {"type": "error", "error": "错误信息"}

```

## 使用效果

### 对比

#### 非流式 (旧版)
```
用户: 投保人需要提供哪些材料?
[等待 3 秒...]
AI: [完整答案一次性显示]
```

#### 流式 (新版)
```
用户: 投保人需要提供哪些材料?
AI: 根▊
AI: 根据契约▊
AI: 根据契约业务规则▊
AI: 根据契约业务规则,投保人需要提供▊
AI: 根据契约业务规则,投保人需要提供以下材料▊
...
AI: 根据契约业务规则,投保人需要提供以下材料:1. 身份证...
```

### 优势

1. **更好的用户体验**
   - 立即看到响应开始
   - 减少等待焦虑
   - 类似真人打字的感觉

2. **更快的感知速度**
   - 虽然总时间相同
   - 但用户感觉更快
   - 可以提前阅读部分内容

3. **更现代的界面**
   - 类似 ChatGPT 的体验
   - 符合用户期望
   - 提升产品档次

## 技术要点

### 1. LangChain 流式 API

```python
# 非流式
response = self.llm.invoke(messages)
answer = response.content

# 流式
for chunk in self.llm.stream(messages):
    if chunk.content:
        yield chunk.content
```

### 2. Server-Sent Events (SSE)

**特点**:
- 单向通信 (服务器 → 客户端)
- 基于 HTTP
- 自动重连
- 文本格式

**格式**:
```
data: {JSON}\n\n
```

**优势**:
- 比 WebSocket 简单
- 不需要额外协议
- 浏览器原生支持

### 3. ReadableStream

**前端读取流式数据**:

```typescript
const reader = response.body?.getReader()
const decoder = new TextDecoder()

while (true) {
  const { done, value } = await reader.read()
  if (done) break
  
  const text = decoder.decode(value, { stream: true })
  // 处理文本
}
```

## 相关文件

### 后端

- `backend/app/services/rag_service.py`
  - `query()` 方法新增 `stream` 参数
  - `_stream_response()` 流式响应生成器

- `backend/app/api/v1/endpoints/knowledge_base.py`
  - 新增 `POST /query/stream` 端点
  - 使用 `StreamingResponse` 返回流式数据

### 前端

- `frontend/src/pages/KnowledgeBase.tsx`
  - `handleAsk()` 方法改为流式接收
  - 新增 `streaming` 状态
  - 新增打字机光标效果
  - 新增 CSS 动画

## 测试要点

### 1. 功能测试

- [ ] 流式输出正常工作
- [ ] 文本逐字显示
- [ ] 光标闪烁效果
- [ ] 来源信息正确显示
- [ ] QA 记录正确保存
- [ ] 反馈功能正常

### 2. 性能测试

- [ ] 长文本流式输出
- [ ] 多轮对话
- [ ] 网络慢速情况
- [ ] 并发请求

### 3. 异常测试

- [ ] 网络中断
- [ ] API 错误
- [ ] 超时处理
- [ ] 空响应

## 使用指南

### 启动服务

```bash
# 后端
cd backend
python main.py

# 前端
cd frontend
npm run dev
```

### 测试流式输出

1. 访问知识问答页面
2. 上传一些测试文档
3. 提问并观察流式输出效果
4. 注意观察:
   - 文本逐字显示
   - 绿色光标闪烁
   - 来源信息展开
   - 反馈按钮可用

### 对比测试

可以保留原有的非流式端点 `/query` 进行对比:

```typescript
// 非流式
await api.post('/knowledge-base/query', { ... })

// 流式
await fetch('/api/v1/knowledge-base/query/stream', { ... })
```

## 后续优化

### 1. 性能优化

- [ ] 添加流式缓存
- [ ] 优化文本块大小
- [ ] 减少状态更新频率

### 2. 功能增强

- [ ] 支持暂停/继续
- [ ] 支持停止生成
- [ ] 支持重新生成
- [ ] 支持语音播报

### 3. 用户体验

- [ ] 添加进度指示
- [ ] 优化光标样式
- [ ] 添加音效
- [ ] 支持自定义速度

## 总结

✅ **已完成**:
- LangChain 流式输出支持
- SSE 格式数据传输
- 前端流式接收和显示
- 打字机光标效果
- 完整的错误处理

🎯 **核心价值**:
- 更好的用户体验
- 更快的感知速度
- 更现代的界面
- 符合行业标准

🚀 **技术亮点**:
- LangChain 原生流式 API
- Server-Sent Events
- ReadableStream
- 实时状态更新

