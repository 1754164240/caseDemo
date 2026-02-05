# 需求导入后生成案例的完整流程

> **文档版本**: v1.0
> **最后更新**: 2026-02-05
> **适用系统**: 智能测试用例平台 v1.3+

本文档详细描述了从需求文档上传到自动化测试用例生成的完整技术流程。

---

## 📋 流程总览

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 需求文档上传 │ -> │  文档解析   │ -> │ 文本向量化  │ -> │ 测试点生成  │ -> │ 测试用例生成 │ -> │ 平台集成创建 │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      ↓                  ↓                  ↓                  ↓                  ↓                  ↓
   前端上传            多格式              Milvus             AI分析             RAG增强            平台API
   保存数据库          解析文本            存储向量           LLM推理            上下文             创建用例
```

**核心技术栈**:
- **文档解析**: LangChain + python-docx + PyPDF2 + openpyxl
- **向量数据库**: Milvus + 硅基流动嵌入 (BAAI/bge-large-zh-v1.5)
- **AI推理**: OpenAI API / 兼容服务 + LangChain 1.0+
- **实时通知**: WebSocket (JWT认证)
- **平台集成**: REST API + 超时保护

---

## 🔄 详细流程说明

### 阶段 1: 需求文档上传与解析

#### 1.1 API入口

**端点**: `POST /api/v1/requirements/`
**代码位置**: [backend/app/api/v1/endpoints/requirements.py](../backend/app/api/v1/endpoints/requirements.py)

**请求参数**:
```json
{
  "file": "multipart/form-data",
  "title": "需求文档标题",
  "description": "需求描述（可选）"
}
```

**响应数据**:
```json
{
  "id": 1,
  "title": "需求文档标题",
  "file_name": "需求文档.docx",
  "file_path": "/uploads/xxxx.docx",
  "status": "pending",
  "created_at": "2026-02-05T10:00:00"
}
```

#### 1.2 文档解析处理

**处理服务**: [backend/app/services/document_parser.py](../backend/app/services/document_parser.py)

**支持格式**:
- ✅ Word文档 (`.docx`)
- ✅ PDF文件 (`.pdf`)
- ✅ 文本文件 (`.txt`)
- ✅ Excel表格 (`.xls`, `.xlsx`)

**解析策略** (三层回退机制):

```python
# 第一层: LangChain工具解析
try:
    if file_extension == '.docx':
        loader = Docx2txtLoader(file_path)
    elif file_extension == '.pdf':
        loader = PyPDFLoader(file_path)
    elif file_extension == '.txt':
        loader = TextLoader(file_path)
    elif file_extension in ['.xls', '.xlsx']:
        loader = UnstructuredExcelLoader(file_path)

    documents = loader.load()
    content = "\n".join([doc.page_content for doc in documents])

except Exception as e:
    # 第二层: LangChain Unstructured解析
    try:
        loader = UnstructuredFileLoader(file_path)
        documents = loader.load()
        content = "\n".join([doc.page_content for doc in documents])

    except Exception as e:
        # 第三层: 原生Python库解析
        if file_extension == '.docx':
            content = parse_docx_native(file_path)
        elif file_extension == '.pdf':
            content = parse_pdf_native(file_path)
        # ...
```

#### 1.3 DOCX特殊处理

**增强功能**:
- 提取段落文本
- 提取表格内容
- 提取页眉页脚
- 提取文本框内容
- 使用XML直接解析复杂格式

**代码示例**:
```python
def parse_docx_native(file_path: str) -> str:
    doc = Document(file_path)
    content = []

    # 提取段落
    for para in doc.paragraphs:
        if para.text.strip():
            content.append(para.text)

    # 提取表格
    for table in doc.tables:
        for row in table.rows:
            row_text = ' | '.join(cell.text for cell in row.cells)
            content.append(row_text)

    # 提取页眉页脚
    for section in doc.sections:
        header = section.header
        for para in header.paragraphs:
            if para.text.strip():
                content.append(para.text)

    # XML解析文本框
    xml_content = doc.element.xml
    # ... 提取文本框内容

    return "\n".join(content)
```

#### 1.4 Excel特殊处理

**智能表头识别**:
```python
def parse_excel_native(file_path: str) -> str:
    wb = openpyxl.load_workbook(file_path)
    content = []

    for sheet in wb.worksheets:
        # 第一行作为表头
        headers = [cell.value for cell in sheet[1]]

        empty_row_count = 0
        for row in sheet.iter_rows(min_row=2):
            row_values = [cell.value for cell in row]

            # 防止大文件卡死: 连续2000空行自动停止
            if all(v is None or str(v).strip() == '' for v in row_values):
                empty_row_count += 1
                if empty_row_count > 2000:
                    break
                continue

            # 格式化为 "列名: 值"
            row_data = []
            for header, value in zip(headers, row_values):
                if header and value:
                    row_data.append(f"{header}: {value}")

            content.append(' | '.join(row_data))

    return "\n".join(content)
```

#### 1.5 输出结果

解析后的纯文本内容存储到数据库 `requirements` 表:

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 主键 |
| `title` | String | 需求标题 |
| `file_name` | String | 原始文件名 |
| `file_path` | String | 文件存储路径 |
| `content` | Text | 解析后的文本内容 |
| `status` | String | 处理状态 (pending/processing/completed) |
| `user_id` | Integer | 用户ID |
| `created_at` | DateTime | 创建时间 |

---

### 阶段 2: 文档向量化与知识库构建

#### 2.1 处理服务

**代码位置**: [backend/app/services/document_embedding_service.py](../backend/app/services/document_embedding_service.py)

**核心参数**:
```python
CHUNK_SIZE = 500           # 每段文本大小
CHUNK_OVERLAP = 100        # 段落重叠 (保证语义连续性)
EMBEDDING_MODEL = "BAAI/bge-large-zh-v1.5"  # 硅基流动中文向量模型
EMBEDDING_DIMENSION = 1536  # 向量维度
```

#### 2.2 文本智能切分

**使用 RecursiveCharacterTextSplitter**:
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=[
        "\n\n",  # 段落分隔符
        "\n",    # 换行符
        "、",    # 中文顿号
        "，",    # 中文逗号
        "；",    # 中文分号
        ".",     # 英文句号
        "!",     # 感叹号
        "?",     # 问号
        ";",     # 英文分号
        "：",    # 中文冒号
        " ",     # 空格
        ""       # 字符级别
    ]
)

chunks = text_splitter.split_text(document_content)
```

**切分示例**:
```
原文 (1200字符):
"保险产品投保规则：1. 投保年龄：18-65周岁；2. 缴费方式：月缴、季缴、年缴..."

切分结果:
[片段 1] (500字符): "保险产品投保规则：1. 投保年龄：18-65周岁；2. 缴费方式：..."
[片段 2] (500字符): "...缴费方式：月缴、季缴、年缴；3. 保险期间：10年、20年..."
[片段 3] (200字符): "...保险期间：10年、20年、30年、终身..."
```

#### 2.3 批量向量化

**调用硅基流动API**:
```python
async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    url = f"{EMBEDDING_API_BASE}/embeddings"
    headers = {
        "Authorization": f"Bearer {EMBEDDING_API_KEY}",
        "Content-Type": "application/json"
    }

    batch_size = 100  # 初始批量大小
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]

        try:
            response = requests.post(
                url,
                headers=headers,
                json={
                    "model": EMBEDDING_MODEL,
                    "input": batch
                },
                timeout=30
            )

            if response.status_code == 413:
                # 智能错误处理: 遇到413错误自动降低batch_size
                logger.warning(f"批量大小 {batch_size} 过大, 减半重试")
                batch_size = batch_size // 2
                continue

            data = response.json()
            embeddings = [item['embedding'] for item in data['data']]
            all_embeddings.extend(embeddings)

        except Exception as e:
            logger.error(f"向量化失败: {e}")
            # 超长文本自动拆分
            if len(batch) > 1:
                batch_size = max(1, batch_size // 2)
                continue

    return all_embeddings
```

#### 2.4 写入Milvus向量数据库

**集合结构** (Collection Schema):
```python
from pymilvus import CollectionSchema, FieldSchema, DataType

fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="requirement_id", dtype=DataType.INT64),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
    FieldSchema(name="chunk_index", dtype=DataType.INT64)
]

schema = CollectionSchema(fields, description="需求文档知识库")
collection = Collection(name="requirement_knowledge", schema=schema)

# 创建索引 (IVF_FLAT)
index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": "L2",
    "params": {"nlist": 128}
}
collection.create_index(field_name="embedding", index_params=index_params)
```

**插入数据**:
```python
entities = [
    [1, 1, 1, ...],                           # requirement_id
    ["文本片段1", "文本片段2", ...],            # text
    [[0.1, 0.2, ...], [0.3, 0.4, ...], ...],  # embedding (1536维向量)
    [0, 1, 2, ...]                            # chunk_index
]

collection.insert(entities)
collection.load()  # 加载到内存
```

#### 2.5 构建AI上下文

**智能抽样策略**:
```python
def build_ai_context(requirement_id: int, max_length: int = 8000) -> str:
    # 从Milvus检索所有文档片段
    collection = Collection("requirement_knowledge")
    results = collection.query(
        expr=f"requirement_id == {requirement_id}",
        output_fields=["text", "chunk_index"]
    )

    # 按chunk_index排序
    chunks = sorted(results, key=lambda x: x['chunk_index'])

    # 智能抽样: 避免超出LLM Token限制
    total_text = ""
    total_length = 0
    step = max(1, len(chunks) // 10)  # 最多抽样10个片段

    for i, chunk in enumerate(chunks[::step]):
        fragment = f"[片段 {i+1}/{len(chunks)}]\n{chunk['text']}\n\n"
        if total_length + len(fragment) > max_length:
            break
        total_text += fragment
        total_length += len(fragment)

    return total_text
```

#### 2.6 WebSocket通知

**通知类型**: `knowledge_base_completed`

```python
await websocket_manager.broadcast(
    user_id=current_user.id,
    message={
        "type": "knowledge_base_completed",
        "requirement_id": requirement_id,
        "chunks_count": len(chunks),
        "status": "success"
    }
)
```

---

### 阶段 3: 测试点生成 (AI分析)

#### 3.1 API端点

**端点**: `POST /api/v1/test-points/generate`
**代码位置**: [backend/app/api/v1/endpoints/test_points.py](../backend/app/api/v1/endpoints/test_points.py)

**请求参数**:
```json
{
  "requirement_id": 1,
  "model_config_id": 1  // 可选, 指定模型配置
}
```

#### 3.2 AI服务初始化

**代码位置**: [backend/app/services/ai_service.py](../backend/app/services/ai_service.py)

**配置优先级**:
```python
1. 数据库 model_configs (优先级最高)
   ↓
2. 环境变量 .env (回退方案)
```

**初始化流程**:
```python
from langchain_openai import init_chat_model

class AIService:
    def __init__(self, model_config_id: Optional[int] = None):
        # 1. 获取模型配置
        if model_config_id:
            config = db.query(ModelConfig).filter_by(id=model_config_id).first()
        else:
            config = db.query(ModelConfig).filter_by(is_default=True).first()

        if config:
            # 使用数据库配置
            api_key = config.api_key
            base_url = config.api_base
            model_name = config.selected_model  # 从多模型配置中选择
        else:
            # 回退到环境变量
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("OPENAI_API_BASE")
            model_name = os.getenv("MODEL_NAME", "gpt-4")

        # 2. 初始化LLM
        self.llm = init_chat_model(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            timeout=180,  # 超时时间: 180秒
            max_retries=3  # 最大重试: 3次
        )
```

#### 3.3 测试点生成流程

**核心方法**: `extract_test_points(requirement_id: int)`

**步骤详解**:

**Step 1: 从Milvus检索需求上下文**
```python
# 构建AI上下文 (最多8000字符)
requirement_context = build_ai_context(requirement_id, max_length=8000)
```

**Step 2: 读取Prompt模板**
```python
# 优先从 system_config 表读取自定义Prompt
prompt_config = db.query(SystemConfig).filter_by(
    config_key="TEST_POINT_PROMPT"
).first()

if prompt_config:
    system_prompt = prompt_config.config_value
else:
    # 使用默认Prompt
    system_prompt = """你是一个专业的保险行业测试专家。

请分析以下需求文档，识别所有需要测试的点。

要求识别以下类型的测试点：
1. **功能性测试点**: 核心功能是否正常工作
2. **边界条件测试点**: 临界值、极值、边界场景
3. **异常情况测试点**: 错误输入、异常流程
4. **业务规则验证点**: 保险规则、计算逻辑、审核流程

对每个测试点，请识别所属业务线：
- contract (契约): 投保、核保、承保
- preservation (保全): 保单变更、退保、复效
- claim (理赔): 报案、理赔审核、赔付

请以JSON数组格式输出，每个测试点包含：
- title: 测试点标题 (简洁明了)
- description: 详细描述 (包含测试目的、覆盖场景)
- category: 类型 (功能/边界/异常/业务规则)
- priority: 优先级 (high/medium/low)
- business_line: 业务线 (contract/preservation/claim)

示例：
[
  {
    "title": "投保年龄边界值测试",
    "description": "测试投保年龄的临界值：18周岁、65周岁，以及超出范围的情况",
    "category": "边界",
    "priority": "high",
    "business_line": "contract"
  }
]
"""
```

**Step 3: 调用LLM生成测试点**
```python
from langchain_core.messages import HumanMessage, SystemMessage

messages = [
    SystemMessage(content=system_prompt),
    HumanMessage(content=f"需求文档内容：\n\n{requirement_context}")
]

response = self.llm.invoke(messages)
```

**Step 4: 增强JSON解析**
```python
def parse_json_response(response_text: str) -> List[dict]:
    """多层解析策略, 增强鲁棒性"""

    # 策略1: 优先提取 [...] 数组部分
    import re
    array_match = re.search(r'\[[\s\S]*\]', response_text)
    if array_match:
        try:
            return json.loads(array_match.group())
        except:
            pass

    # 策略2: 尝试解析完整响应
    try:
        return json.loads(response_text)
    except:
        pass

    # 策略3: 提取markdown代码块
    code_block_match = re.search(r'```json\n([\s\S]*?)\n```', response_text)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except:
            pass

    # 策略4: 失败时返回示例数据 (避免前端崩溃)
    logger.warning(f"JSON解析失败, 返回示例数据")
    return [
        {
            "title": "解析失败-请手动检查",
            "description": "AI响应格式异常，请查看日志",
            "category": "功能",
            "priority": "medium",
            "business_line": "contract"
        }
    ]
```

**Step 5: 保存到数据库**
```python
test_points = []
for point_data in parsed_response:
    test_point = TestPoint(
        requirement_id=requirement_id,
        title=point_data['title'],
        description=point_data['description'],
        category=point_data['category'],
        priority=point_data['priority'],
        business_line=point_data.get('business_line', 'contract'),
        status='pending',  # 初始状态: 待审批
        user_id=current_user.id
    )
    db.add(test_point)
    test_points.append(test_point)

db.commit()
```

**Step 6: WebSocket实时推送**
```python
await websocket_manager.broadcast(
    user_id=current_user.id,
    message={
        "type": "test_points_generated",
        "requirement_id": requirement_id,
        "test_points_count": len(test_points),
        "status": "success"
    }
)
```

#### 3.4 重试机制

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),  # 最大重试3次
    wait=wait_exponential(multiplier=1, min=2, max=10),  # 指数退避
    reraise=True
)
def call_llm_with_retry(messages):
    return llm.invoke(messages)
```

#### 3.5 性能指标

**记录详细日志**:
```python
import time

start_time = time.time()
response = self.llm.invoke(messages)
elapsed_time = time.time() - start_time

logger.info(f"测试点生成完成: requirement_id={requirement_id}, "
            f"耗时={elapsed_time:.2f}秒, "
            f"测试点数量={len(test_points)}")
```

---

### 阶段 4: 测试用例生成 (RAG增强)

#### 4.1 API端点

**端点**: `POST /api/v1/test-cases/generate`
**代码位置**: [backend/app/api/v1/endpoints/test_cases.py](../backend/app/api/v1/endpoints/test_cases.py)

**请求参数**:
```json
{
  "test_point_ids": [1, 2, 3],  // 测试点ID列表
  "model_config_id": 1           // 可选
}
```

#### 4.2 RAG检索增强

**代码位置**: [backend/app/services/rag_service.py](../backend/app/services/rag_service.py)

**检索流程**:

**Step 1: 生成查询向量**
```python
def generate_query_embedding(test_point: TestPoint) -> List[float]:
    query_text = f"{test_point.title}\n{test_point.description}"

    response = requests.post(
        f"{EMBEDDING_API_BASE}/embeddings",
        headers={"Authorization": f"Bearer {EMBEDDING_API_KEY}"},
        json={
            "model": EMBEDDING_MODEL,
            "input": [query_text]
        }
    )

    return response.json()['data'][0]['embedding']
```

**Step 2: 从Milvus检索相关文档**
```python
def retrieve_relevant_context(
    requirement_id: int,
    query_embedding: List[float],
    top_k: int = 5
) -> str:
    collection = Collection("requirement_knowledge")

    # 向量相似度搜索
    search_params = {
        "metric_type": "L2",
        "params": {"nprobe": 10}
    }

    results = collection.search(
        data=[query_embedding],
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        expr=f"requirement_id == {requirement_id}",
        output_fields=["text"]
    )

    # 拼接所有相关片段
    context_parts = []
    for i, hit in enumerate(results[0]):
        context_parts.append(f"[相关片段 {i+1}]\n{hit.entity.get('text')}\n")

    return "\n".join(context_parts)
```

#### 4.3 业务线智能识别

**根据测试点的 `business_line` 字段选择Prompt**:

```python
def get_test_case_prompt(business_line: str) -> str:
    # Prompt配置键映射
    prompt_key_mapping = {
        "contract": "CONTRACT_TEST_CASE_PROMPT",        # 契约业务
        "preservation": "PRESERVATION_TEST_CASE_PROMPT", # 保全业务
        "claim": "CLAIM_TEST_CASE_PROMPT",              # 理赔业务
    }

    prompt_key = prompt_key_mapping.get(business_line, "TEST_CASE_PROMPT")

    # 从 system_config 表读取
    config = db.query(SystemConfig).filter_by(config_key=prompt_key).first()

    if config:
        return config.config_value
    else:
        # 使用默认通用模板
        return get_default_test_case_prompt()
```

#### 4.4 测试用例生成Prompt

**默认Prompt模板**:
```python
def get_default_test_case_prompt() -> str:
    return """你是一个专业的保险行业测试工程师。

请根据以下测试点和需求上下文，设计详细的测试用例。

测试点信息：
- 标题：{title}
- 描述：{description}
- 分类：{category}
- 优先级：{priority}

需求上下文：
{context}

请为该测试点生成 2-3 个测试用例，覆盖以下场景：
1. **正常流程**: 标准业务流程
2. **边界条件**: 临界值、极值场景
3. **异常场景**: 错误输入、异常流程

每个测试用例包含：
- title: 用例标题 (明确、具体)
- description: 用例描述
- preconditions: 前置条件 (测试前需要满足的条件)
- test_steps: 测试步骤 (数组格式)
  - step: 步骤序号
  - action: 操作描述
  - expected: 预期结果
- expected_result: 总体预期结果
- priority: 优先级 (high/medium/low)
- test_type: 测试类型 (functional/boundary/exception)

输出JSON格式：
[
  {
    "title": "正常投保流程-月缴",
    "description": "验证正常投保流程，选择月缴方式",
    "preconditions": "1. 用户已登录；2. 产品可投保",
    "test_steps": [
      {
        "step": 1,
        "action": "进入产品投保页面",
        "expected": "页面正常展示产品信息"
      },
      {
        "step": 2,
        "action": "填写投保人信息：姓名、身份证、年龄30岁",
        "expected": "信息填写成功"
      },
      {
        "step": 3,
        "action": "选择缴费方式：月缴",
        "expected": "月缴方式选中，显示对应保费"
      },
      {
        "step": 4,
        "action": "提交投保申请",
        "expected": "投保成功，生成保单号"
      }
    ],
    "expected_result": "投保流程正常完成，保单状态为待核保",
    "priority": "high",
    "test_type": "functional"
  }
]
"""
```

#### 4.5 调用LLM生成用例

```python
def generate_test_cases(test_point_id: int) -> List[TestCase]:
    # 1. 获取测试点
    test_point = db.query(TestPoint).filter_by(id=test_point_id).first()

    # 2. RAG检索相关需求上下文
    query_embedding = generate_query_embedding(test_point)
    context = retrieve_relevant_context(
        test_point.requirement_id,
        query_embedding,
        top_k=5
    )

    # 3. 获取Prompt模板
    system_prompt = get_test_case_prompt(test_point.business_line)

    # 4. 构建消息
    user_message = system_prompt.format(
        title=test_point.title,
        description=test_point.description,
        category=test_point.category,
        priority=test_point.priority,
        context=context
    )

    messages = [
        SystemMessage(content="你是一个专业的测试工程师"),
        HumanMessage(content=user_message)
    ]

    # 5. 调用LLM
    response = self.llm.invoke(messages)

    # 6. 解析JSON响应
    test_cases_data = parse_json_response(response.content)

    # 7. 保存到数据库
    test_cases = []
    for case_data in test_cases_data:
        test_case = TestCase(
            test_point_id=test_point_id,
            requirement_id=test_point.requirement_id,
            title=case_data['title'],
            description=case_data['description'],
            preconditions=case_data['preconditions'],
            test_steps=json.dumps(case_data['test_steps'], ensure_ascii=False),
            expected_result=case_data['expected_result'],
            priority=case_data['priority'],
            test_type=case_data['test_type'],
            status='pending',
            user_id=current_user.id
        )
        db.add(test_case)
        test_cases.append(test_case)

    db.commit()

    # 8. WebSocket通知
    await websocket_manager.broadcast(
        user_id=current_user.id,
        message={
            "type": "test_case_generated",
            "test_point_id": test_point_id,
            "test_cases_count": len(test_cases)
        }
    )

    return test_cases
```

#### 4.6 生成策略

**每个测试点生成 2-3 个测试用例**:
- ✅ 正常流程用例 (功能性)
- ✅ 边界条件用例 (边界值)
- ✅ 异常场景用例 (异常处理)

---

### 阶段 5: 自动化平台集成 (关键流程)

#### 5.1 处理服务

**代码位置**: [backend/app/services/automation_service.py](../backend/app/services/automation_service.py)
**API端点**: [backend/app/api/v1/endpoints/automation_workflow.py](../backend/app/api/v1/endpoints/automation_workflow.py)

#### 5.2 核心方法

**方法签名**:
```python
def create_case_with_fields(
    scene_id: int,
    test_case_info: dict
) -> dict:
    """
    自动化平台集成: 创建用例和明细

    Args:
        scene_id: 自动化平台场景ID
        test_case_info: 测试用例信息
            {
                "title": "用例标题",
                "description": "用例描述",
                "test_steps": [...],
                "expected_result": "预期结果"
            }

    Returns:
        {
            "success": True/False,
            "case_id": "创建的用例ID",
            "message": "处理消息"
        }
    """
```

#### 5.3 详细流程

##### **Step 1: 获取场景用例列表**

```python
def get_scene_cases(scene_id: int) -> List[dict]:
    """从自动化平台获取场景下所有可用用例模板"""

    url = f"{AUTOMATION_PLATFORM_API_BASE}/ai/case/queryBySceneId/{scene_id}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    if data['code'] == 200:
        return data['data']  # 用例列表
    else:
        raise Exception(f"获取场景用例失败: {data['message']}")
```

**返回数据示例**:
```json
[
  {
    "usercaseId": 1001,
    "name": "人寿保险投保用例",
    "description": "用于测试人寿保险投保流程，包含投保人信息、被保险人信息、缴费方式等",
    "sceneId": 100
  },
  {
    "usercaseId": 1002,
    "name": "意外险投保用例",
    "description": "用于测试意外险投保流程...",
    "sceneId": 100
  }
]
```

##### **Step 2: AI选择最匹配用例 (180秒超时保护)**

**超时保护机制**:
```python
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import logging

def select_best_case_by_ai(
    test_case_info: dict,
    available_cases: List[dict]
) -> dict:
    """AI选择最匹配的用例模板"""

    # 优化: 如果只有1个用例，直接返回
    if len(available_cases) == 1:
        logger.info("只有1个可用用例，跳过AI选择")
        return available_cases[0]

    # 优化Prompt: 减少约70% Token使用
    cases_for_ai = [
        {
            'id': str(c.get('usercaseId')),
            'name': str(c.get('name')),
            'desc': str(c.get('description', ''))[:150]  # 截断描述
        }
        for c in available_cases
    ]

    test_title = test_case_info.get('title', '')[:100]
    test_desc = test_case_info.get('description', '')[:200]

    prompt = f"""请从以下用例模板中选择最匹配的一个：

测试用例信息：
标题：{test_title}
描述：{test_desc}

可用模板：
{json.dumps(cases_for_ai, ensure_ascii=False)}

请返回最匹配模板的ID（只返回数字）。
"""

    # 使用线程池 + 超时保护
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(call_ai_to_select, prompt)

        try:
            # 180秒超时
            selected_id = future.result(timeout=180)

            # 查找对应用例
            for case in available_cases:
                if str(case['usercaseId']) == str(selected_id):
                    logger.info(f"AI选择用例成功: {case['name']}")
                    return case

            # 未找到，使用第一个
            logger.warning(f"AI返回的ID {selected_id} 未找到，使用第一个用例")
            return available_cases[0]

        except FutureTimeoutError:
            # 超时降级策略
            logger.warning("AI选择用例超时（180秒），使用第一个可用用例")
            return available_cases[0]

        except Exception as e:
            # 其他异常降级
            logger.error(f"AI选择用例失败: {e}，使用第一个可用用例")
            return available_cases[0]


def call_ai_to_select(prompt: str) -> str:
    """调用AI选择用例"""
    messages = [
        SystemMessage(content="你是用例选择专家，只返回最匹配的用例ID数字"),
        HumanMessage(content=prompt)
    ]

    response = llm.invoke(messages)

    # 提取数字ID
    import re
    match = re.search(r'\d+', response.content)
    if match:
        return match.group()
    else:
        raise ValueError("AI未返回有效ID")
```

##### **Step 3: 获取用例详情**

```python
def get_case_detail(usercase_id: int) -> dict:
    """获取用例详情（含header和body模板）"""

    url = f"{AUTOMATION_PLATFORM_API_BASE}/ai/case/queryCaseBody/{usercase_id}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()

    if data['code'] == 200:
        return data['data']  # 包含 caseDefine 结构
    else:
        raise Exception(f"获取用例详情失败: {data['message']}")
```

**返回数据结构 (caseDefine)**:
```json
{
  "usercaseId": 1001,
  "name": "人寿保险投保用例",
  "caseDefine": {
    "header": [
      {
        "rowName": "投保人姓名",
        "row": "applicantName",
        "type": "String",
        "flag": "input"
      },
      {
        "rowName": "投保人年龄",
        "row": "applicantAge",
        "type": "Integer",
        "flag": "input"
      },
      {
        "rowName": "缴费方式",
        "row": "paymentMode",
        "type": "String",
        "flag": "select",
        "options": ["月缴", "季缴", "年缴"]
      }
    ],
    "body": [
      {
        "casedesc": "正常投保-月缴",
        "casezf": "1",
        "hoperesult": "投保成功",
        "var": {
          "applicantName": "张三",
          "applicantAge": 30,
          "paymentMode": "月缴"
        },
        "iscaserun": true,
        "caseBodySN": 1
      }
    ]
  }
}
```

##### **Step 4: AI生成测试数据 (Body)**

**增强版生成（V2）**:
```python
def generate_case_body_by_ai(
    header_fields: List[dict],
    test_case_info: dict
) -> List[dict]:
    """AI生成测试数据（body）"""

    # 提取字段信息
    fields_info = []
    for field in header_fields:
        field_desc = f"- {field['rowName']} ({field['row']}): 类型={field['type']}"

        # 添加枚举值约束
        if 'options' in field:
            field_desc += f", 可选值={field['options']}"

        # 添加必填标识
        if field.get('required'):
            field_desc += ", 必填"

        fields_info.append(field_desc)

    # 构建Prompt
    prompt = f"""请根据测试用例信息和字段定义，生成真实、合理的测试数据。

测试用例信息：
标题：{test_case_info['title']}
描述：{test_case_info['description']}
测试步骤：
{json.dumps(test_case_info.get('test_steps', []), ensure_ascii=False, indent=2)}

字段定义：
{chr(10).join(fields_info)}

要求：
1. 根据测试用例具体内容生成数据
2. 数据真实、合理、符合业务逻辑
3. 生成1-3条测试数据，覆盖不同场景
4. 字段值符合类型和业务含义
5. 日期使用YYYYMMDD格式（使用current_date_yyyymmdd_tool工具获取当前日期）
6. 遵守字段联动规则（如有）

输出JSON格式：
[
  {{
    "casedesc": "测试角度/场景描述（如'正常投保-月缴'、'年龄边界值测试'）",
    "casezf": "1",  // 1=正向用例, 0=反向用例
    "hoperesult": "预期结果",
    "var": {{
      "字段名1": "值1",
      "字段名2": "值2"
    }},
    "iscaserun": true,
    "caseBodySN": 1
  }}
]
"""

    # 绑定工具（日期/时间）
    tools = [
        current_date_tool,
        current_datetime_tool,
        current_date_yyyymmdd_tool
    ]

    llm_with_tools = llm.bind_tools(tools)

    messages = [
        SystemMessage(content="你是测试数据生成专家"),
        HumanMessage(content=prompt)
    ]

    # 调用LLM
    response = llm_with_tools.invoke(messages)

    # 增强JSON解析
    body_data = parse_agent_response(response.content)

    return body_data
```

**Agent工具定义**:
```python
from langchain.tools import tool
from datetime import datetime

@tool
def current_date_yyyymmdd_tool() -> str:
    """获取当前日期，YYYYMMDD格式"""
    return datetime.now().strftime("%Y%m%d")

@tool
def current_date_tool() -> str:
    """获取当前日期，YYYY-MM-DD格式"""
    return datetime.now().strftime("%Y-%m-%d")

@tool
def current_datetime_tool() -> str:
    """获取当前日期时间，YYYY-MM-DD HH:MM:SS格式"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

**增强JSON解析**:
```python
def parse_agent_response(response_text: str) -> List[dict]:
    """多层解析策略，处理Agent结构化响应"""

    # 策略1: 提取 detail='[...]' (Agent结构化响应)
    import re
    detail_match = re.search(r"detail='(\[[\s\S]*?\])'", response_text)
    if detail_match:
        try:
            json_str = detail_match.group(1)
            # 处理转义字符
            json_str = json_str.replace('\\n', '\n')
            return json.loads(json_str)
        except:
            pass

    # 策略2: 提取 answer='...'
    answer_match = re.search(r"answer='([\s\S]*?)'", response_text)
    if answer_match:
        try:
            json_str = answer_match.group(1)
            return json.loads(json_str)
        except:
            pass

    # 策略3: 提取 markdown代码块 ```json...```
    code_block_match = re.search(r'```json\n([\s\S]*?)\n```', response_text)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except:
            pass

    # 策略4: 直接解析整体
    try:
        return json.loads(response_text)
    except:
        pass

    # 策略5: 归一化处理 \n 转义
    try:
        normalized = response_text.replace('\\n', '\n')
        return json.loads(normalized)
    except:
        pass

    # 策略6: 兜底提取 [...] 或 {...} 片段
    array_match = re.search(r'\[[\s\S]*\]', response_text)
    if array_match:
        try:
            return json.loads(array_match.group())
        except:
            pass

    # 失败时抛出异常
    raise ValueError(f"无法解析AI响应为JSON: {response_text[:200]}")
```

##### **Step 5: 创建用例和明细**

```python
def create_case_and_body(
    usercase_id: int,
    case_define: dict
) -> dict:
    """调用自动化平台API创建用例"""

    url = f"{AUTOMATION_PLATFORM_API_BASE}/ai/case/createCaseAndBody"

    payload = {
        "usercaseId": usercase_id,
        "caseDefine": case_define
    }

    response = requests.post(
        url,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if data['code'] == 200:
        logger.info(f"创建用例成功: case_id={data['data']['caseId']}")
        return {
            "success": True,
            "case_id": data['data']['caseId'],
            "message": "创建成功"
        }
    else:
        logger.error(f"创建用例失败: {data['message']}")
        return {
            "success": False,
            "message": data['message']
        }
```

#### 5.4 完整流程代码

```python
def create_case_with_fields(
    scene_id: int,
    test_case_info: dict
) -> dict:
    """完整流程: 从测试用例到自动化平台用例"""

    try:
        # Step 1: 获取场景用例列表
        logger.info(f"Step 1: 获取场景 {scene_id} 的用例列表")
        available_cases = get_scene_cases(scene_id)

        if not available_cases:
            return {"success": False, "message": "该场景下没有可用用例"}

        # Step 2: AI选择最匹配用例（180秒超时保护）
        logger.info(f"Step 2: AI选择最匹配用例（共 {len(available_cases)} 个可选）")
        selected_case = select_best_case_by_ai(test_case_info, available_cases)

        # Step 3: 获取用例详情
        logger.info(f"Step 3: 获取用例详情 (usercaseId={selected_case['usercaseId']})")
        case_detail = get_case_detail(selected_case['usercaseId'])

        header_fields = case_detail['caseDefine']['header']

        # Step 4: AI生成测试数据
        logger.info(f"Step 4: AI生成测试数据（共 {len(header_fields)} 个字段）")
        generated_body = generate_case_body_by_ai(header_fields, test_case_info)

        # Step 5: 创建用例和明细
        logger.info(f"Step 5: 创建用例和明细（共 {len(generated_body)} 条数据）")
        new_case_define = {
            "header": header_fields,
            "body": generated_body
        }

        result = create_case_and_body(
            selected_case['usercaseId'],
            new_case_define
        )

        return result

    except Exception as e:
        logger.error(f"创建用例失败: {e}", exc_info=True)
        return {
            "success": False,
            "message": f"创建失败: {str(e)}"
        }
```

#### 5.5 自动化平台API集成

**基础配置**:
```python
# 从 system_config 表或环境变量读取
AUTOMATION_PLATFORM_API_BASE = get_config_value(
    "AUTOMATION_PLATFORM_API_BASE",
    default=os.getenv("AUTOMATION_PLATFORM_API_BASE")
)
```

**关键API端点**:

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/ai/case/queryBySceneId/{sceneId}` | 获取场景用例列表 |
| GET | `/ai/case/queryCaseBody/{id}` | 获取用例详情 |
| POST | `/ai/case/createCaseAndBody` | 创建用例和明细 |
| GET | `/ai/case/queryAllScenes` | 获取所有场景 |

**错误处理**:
```python
# 连接超时: 30秒
# HTTP状态检查
# JSON解析验证
# 详细日志记录
```

---

## 🔧 关键技术特性

### 1. 多模型配置支持

**数据库结构** (`model_configs` 表):
```sql
CREATE TABLE model_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    api_key TEXT NOT NULL,
    api_base TEXT NOT NULL,
    model_name JSONB NOT NULL,  -- JSON数组: ["gpt-4", "gpt-3.5-turbo"]
    selected_model VARCHAR(100) NOT NULL,  -- 当前使用的模型
    temperature DECIMAL(3,2),
    is_default BOOLEAN DEFAULT FALSE,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**配置优先级**:
```
数据库 model_configs (优先级最高)
    ↓
环境变量 .env (回退方案)
```

### 2. 配置化Prompt

**所有Prompt可从 `system_config` 表动态读取**:

| 配置键 | 说明 |
|--------|------|
| `TEST_POINT_PROMPT` | 测试点生成Prompt |
| `CONTRACT_TEST_CASE_PROMPT` | 契约业务用例Prompt |
| `PRESERVATION_TEST_CASE_PROMPT` | 保全业务用例Prompt |
| `CLAIM_TEST_CASE_PROMPT` | 理赔业务用例Prompt |
| `TEST_CASE_PROMPT` | 默认通用用例Prompt |

**动态读取示例**:
```python
def get_prompt_from_config(prompt_key: str, default: str) -> str:
    config = db.query(SystemConfig).filter_by(config_key=prompt_key).first()
    return config.config_value if config else default
```

### 3. Agent工具调用

**内置工具**:
```python
# 日期/时间工具
- current_date_tool: 获取当前日期 (YYYY-MM-DD)
- current_datetime_tool: 获取当前日期时间 (YYYY-MM-DD HH:MM:SS)
- current_date_yyyymmdd_tool: 获取YYYYMMDD格式日期
```

**工具绑定**:
```python
from langchain.tools import tool

tools = [current_date_tool, current_datetime_tool, current_date_yyyymmdd_tool]
llm_with_tools = llm.bind_tools(tools)

response = llm_with_tools.invoke(messages)
```

### 4. WebSocket实时推送

**连接格式**:
```
ws://localhost:8000/api/v1/ws/{client_id}?token={jwt_token}
```

**消息类型**:

| 类型 | 说明 | 数据结构 |
|------|------|----------|
| `knowledge_base_completed` | 知识库构建完成 | `{requirement_id, chunks_count, status}` |
| `test_points_generated` | 测试点生成完成 | `{requirement_id, test_points_count, status}` |
| `test_case_generated` | 测试用例生成完成 | `{test_point_id, test_cases_count}` |

**前端实现** ([frontend/src/stores/websocketStore.ts](../frontend/src/stores/websocketStore.ts)):
```typescript
import { create } from 'zustand';

interface WebSocketStore {
  ws: WebSocket | null;
  isConnected: boolean;
  connect: (clientId: string, token: string) => void;
  disconnect: () => void;
}

export const useWebSocketStore = create<WebSocketStore>((set, get) => ({
  ws: null,
  isConnected: false,

  connect: (clientId: string, token: string) => {
    const ws = new WebSocket(
      `ws://localhost:8000/api/v1/ws/${clientId}?token=${token}`
    );

    ws.onopen = () => {
      console.log('WebSocket连接成功');
      set({ isConnected: true });
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log('收到消息:', message);

      // 处理不同消息类型
      switch (message.type) {
        case 'test_points_generated':
          // 刷新测试点列表
          break;
        case 'test_case_generated':
          // 刷新测试用例列表
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket错误:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket连接关闭');
      set({ isConnected: false });

      // 自动重连机制
      setTimeout(() => get().connect(clientId, token), 3000);
    };

    set({ ws });
  },

  disconnect: () => {
    const { ws } = get();
    if (ws) {
      ws.close();
      set({ ws: null, isConnected: false });
    }
  }
}));
```

---

## ⚡ 性能优化措施

### 1. 批量向量化

**动态调整batch_size**:
```python
batch_size = 100  # 初始批量大小

while texts_to_process:
    try:
        # 批量向量化
        embeddings = generate_embeddings(texts[:batch_size])

    except RequestEntityTooLarge:  # HTTP 413
        # 动态降低批量大小
        batch_size = batch_size // 2
        logger.warning(f"批量大小过大，调整为 {batch_size}")
```

### 2. Milvus向量检索优化

**索引配置**:
```python
# IVF_FLAT索引: 高召回率
index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": "L2",
    "params": {"nlist": 128}
}

# 搜索参数
search_params = {
    "metric_type": "L2",
    "params": {"nprobe": 10}  # 检索的聚类数量
}
```

### 3. AI调用超时保护

**180秒超时 + 降级策略**:
```python
from concurrent.futures import ThreadPoolExecutor, TimeoutError

with ThreadPoolExecutor(max_workers=1) as executor:
    future = executor.submit(call_ai)

    try:
        result = future.result(timeout=180)
    except TimeoutError:
        # 降级: 使用默认值
        result = get_default_value()
```

### 4. Prompt优化

**减少约70% Token使用**:
```python
# 优化前: 完整描述
case = {
    'id': 1001,
    'name': "人寿保险投保用例",
    'description': "用于测试人寿保险投保流程，包含投保人信息、被保险人信息、缴费方式、保险金额、保险期间等多个字段的验证，支持月缴、季缴、年缴多种缴费方式..."  # 300+字符
}

# 优化后: 截断描述
case = {
    'id': 1001,
    'name': "人寿保险投保用例",
    'desc': "用于测试人寿保险投保流程，包含投保人信息、被保险人信息、缴费方式..."[:150]  # 150字符
}
```

### 5. 异步处理

**使用 ThreadPoolExecutor 避免阻塞**:
```python
from concurrent.futures import ThreadPoolExecutor

# 并发处理多个测试点
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(generate_test_cases, test_point_id)
        for test_point_id in test_point_ids
    ]

    results = [future.result() for future in futures]
```

### 6. 错误重试

**最大3次重试 + 指数退避**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_llm_with_retry(messages):
    return llm.invoke(messages)
```

---

## 🛡️ 容错机制

### 1. 文档解析容错

**三层回退策略**:
```
LangChain工具解析
    ↓ 失败
LangChain Unstructured解析
    ↓ 失败
原生Python库解析
```

### 2. AI调用失败容错

**返回示例数据，避免前端崩溃**:
```python
try:
    response = llm.invoke(messages)
    data = parse_json_response(response.content)
except Exception as e:
    logger.error(f"AI调用失败: {e}")
    # 返回示例数据
    data = [
        {
            "title": "AI生成失败-示例测试点",
            "description": "请手动编辑",
            "category": "功能",
            "priority": "medium"
        }
    ]
```

### 3. 向量化失败容错

**记录警告，继续后续流程**:
```python
try:
    embeddings = generate_embeddings(texts)
    milvus_service.insert(embeddings)
except Exception as e:
    logger.warning(f"向量化失败: {e}")
    # 不影响后续流程，仅记录警告
```

### 4. JSON解析容错

**多种提取策略**:
```python
# 1. 提取 [...] 数组
# 2. 提取 markdown代码块
# 3. 提取 detail='...'
# 4. 直接解析
# 5. 归一化处理
# 6. 兜底提取
```

### 5. 超时降级

**AI超时自动使用第一个可用选项**:
```python
try:
    selected = select_best_case_by_ai(test_case, cases)
except TimeoutError:
    # 降级: 使用第一个用例
    selected = cases[0]
```

---

## 📊 数据流图

```
┌──────────────────┐
│  需求文档上传     │
│  (DOCX/PDF/TXT)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│   文档解析        │
│ (DocumentParser) │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐       ┌──────────────────┐
│   文本切分        │       │  硅基流动嵌入API  │
│ (TextSplitter)   │──────>│  (Embedding)     │
└────────┬─────────┘       └──────────────────┘
         │                          │
         │                          ▼
         │                 ┌──────────────────┐
         │                 │   Milvus向量库    │
         │                 │  (1536维向量)    │
         │                 └────────┬─────────┘
         │                          │
         ▼                          ▼
┌──────────────────┐       ┌──────────────────┐
│  测试点生成       │<──────│   RAG检索        │
│  (AI分析)        │       │  (向量相似度)     │
└────────┬─────────┘       └──────────────────┘
         │
         ▼
┌──────────────────┐       ┌──────────────────┐
│  测试用例生成     │<──────│   RAG增强        │
│  (AI生成)        │       │  (上下文检索)     │
└────────┬─────────┘       └──────────────────┘
         │
         ▼
┌──────────────────┐
│  自动化平台集成   │
│  (创建用例)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  自动化测试用例   │
│  (可执行)        │
└──────────────────┘
```

---

## 📂 关键文件索引

| 阶段 | 文件路径 | 功能 | 关键方法 |
|------|----------|------|----------|
| **文档上传** | [requirements.py](../backend/app/api/v1/endpoints/requirements.py) | API端点 | `create_requirement` |
| **文档解析** | [document_parser.py](../backend/app/services/document_parser.py) | 多格式解析 | `parse_document` |
| **向量化** | [document_embedding_service.py](../backend/app/services/document_embedding_service.py) | Milvus存储 | `embed_document` |
| **Milvus服务** | [milvus_service.py](../backend/app/services/milvus_service.py) | 向量数据库 | `insert`, `search` |
| **测试点生成** | [ai_service.py](../backend/app/services/ai_service.py) | LLM分析 | `extract_test_points` |
| **测试用例生成** | [ai_service.py](../backend/app/services/ai_service.py) | RAG增强 | `generate_test_cases` |
| **RAG服务** | [rag_service.py](../backend/app/services/rag_service.py) | 上下文检索 | `retrieve_context` |
| **平台集成** | [automation_service.py](../backend/app/services/automation_service.py) | 自动化创建 | `create_case_with_fields` |
| **WebSocket** | [websocket_service.py](../backend/app/services/websocket_service.py) | 实时通知 | `broadcast` |

---

## 🔍 调试和监控

### 日志配置

```python
import logging

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 关键节点记录
logger.info(f"文档解析完成: {file_name}, 内容长度={len(content)}")
logger.info(f"向量化完成: requirement_id={req_id}, 片段数={len(chunks)}")
logger.info(f"测试点生成: requirement_id={req_id}, 数量={len(points)}, 耗时={elapsed:.2f}秒")
```

### 性能监控

```python
import time

def performance_monitor(func):
    """性能监控装饰器"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time

        logger.info(f"{func.__name__} 执行完成, 耗时={elapsed:.2f}秒")
        return result
    return wrapper

@performance_monitor
def extract_test_points(requirement_id):
    # ...
```

---

## 📚 相关文档

- [快速开始](QUICK_START.md)
- [系统架构](ARCHITECTURE.md)
- [多模型配置](MULTI_MODEL_CONFIG.md)
- [AI选择超时修复](AI_SELECTION_TIMEOUT_FIX.md)
- [测试数据生成](TEST_DATA_GENERATION.md)
- [问题排查指南](TROUBLESHOOTING.md)

---

## ❓ 常见问题

### Q1: 文档解析失败怎么办？

**A**: 系统有三层回退机制:
1. 检查文档格式是否支持 (DOCX/PDF/TXT/XLS/XLSX)
2. 查看日志，确认具体错误
3. 尝试转换为TXT格式后重新上传

### Q2: 向量化速度慢怎么办？

**A**:
1. 检查硅基流动API配额
2. 调整 `CHUNK_SIZE` 参数 (默认500)
3. 监控 `batch_size` 动态调整日志

### Q3: AI生成的测试点不准确？

**A**:
1. 检查需求文档质量，补充详细信息
2. 在 `system_config` 表自定义 `TEST_POINT_PROMPT`
3. 调整模型配置，使用更强大的模型 (如 GPT-4)

### Q4: 自动化平台集成失败？

**A**:
1. 检查 `AUTOMATION_PLATFORM_API_BASE` 配置
2. 查看 API 连接日志
3. 确认场景ID和用例模板是否存在

---

**文档结束**