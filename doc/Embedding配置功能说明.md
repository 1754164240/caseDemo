# Embedding 配置功能说明

## ✅ 功能已实现!

### 功能描述
支持为 Embedding 模型配置**单独的 API Key 和 API Base**,允许 LLM 和 Embedding 使用不同的服务提供商。

### 使用场景

#### 场景 1: LLM 和 Embedding 使用同一个服务 ✅
**示例**: 都使用 ModelScope

**配置**:
- **LLM 配置**:
  - API Key: `ms-1edea540-3aa5-4757-be16-11e2ddb5abbe`
  - API Base: `https://api-inference.modelscope.cn/v1`
  - Model: `deepseek-ai/DeepSeek-V3.1`

- **Embedding 配置**:
  - Model: `BAAI/bge-small-zh-v1.5`
  - API Key: **(留空,自动使用 LLM 的 API Key)**
  - API Base: **(留空,自动使用 LLM 的 API Base)**

**优点**: 配置简单,只需维护一套 API 凭证

---

#### 场景 2: LLM 和 Embedding 使用不同服务 ✅
**示例**: LLM 使用 ModelScope, Embedding 使用 OpenAI

**配置**:
- **LLM 配置**:
  - API Key: `ms-1edea540-3aa5-4757-be16-11e2ddb5abbe`
  - API Base: `https://api-inference.modelscope.cn/v1`
  - Model: `deepseek-ai/DeepSeek-V3.1`

- **Embedding 配置**:
  - Model: `text-embedding-ada-002`
  - API Key: `sk-proj-xxxxxxxxxxxxx` **(OpenAI API Key)**
  - API Base: `https://api.openai.com/v1` **(OpenAI API Base)**

**优点**: 灵活选择最优服务,LLM 用国内服务(快),Embedding 用 OpenAI(精度高)

---

#### 场景 3: 使用本地 Embedding 模型 ✅
**示例**: LLM 使用 ModelScope, Embedding 使用本地 Ollama

**配置**:
- **LLM 配置**:
  - API Key: `ms-1edea540-3aa5-4757-be16-11e2ddb5abbe`
  - API Base: `https://api-inference.modelscope.cn/v1`
  - Model: `deepseek-ai/DeepSeek-V3.1`

- **Embedding 配置**:
  - Model: `nomic-embed-text`
  - API Key: `ollama` **(任意值,Ollama 不验证)**
  - API Base: `http://localhost:11434/v1` **(本地 Ollama 服务)**

**优点**: 降低成本,Embedding 完全本地化,无需调用外部 API

---

### 配置方式

#### 方式 1: 系统管理页面配置 (推荐) ✅

1. **登录系统**
   - 使用超级管理员账号登录 (admin / admin123)

2. **进入系统管理**
   - 点击左侧菜单 "系统管理"

3. **配置 LLM**
   - 点击 "模型配置" Tab
   - 填写:
     - API Key: `ms-1edea540-3aa5-4757-be16-11e2ddb5abbe`
     - API Base URL: `https://api-inference.modelscope.cn/v1`
     - 模型名称: `deepseek-ai/DeepSeek-V3.1`
   - 点击 "保存配置"

4. **配置 Embedding**
   - 点击 "Embedding 配置" Tab
   - 填写:
     - Embedding 模型名称: `BAAI/bge-small-zh-v1.5`
     - Embedding API Key: **(留空或填写单独的 Key)**
     - Embedding API Base URL: **(留空或填写单独的 URL)**
   - 点击 "保存配置"

5. **重启后端**
   - 配置会立即保存到数据库和 `.env` 文件
   - 部分配置需要重启后端才能完全生效

---

#### 方式 2: 数据库直接配置

```python
from app.db.session import SessionLocal
from app.models.system_config import SystemConfig

db = SessionLocal()

# 配置 Embedding 模型
configs = [
    ("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5", "Embedding 模型名称"),
    ("EMBEDDING_API_KEY", "", "Embedding API Key (为空时使用 LLM 的 API Key)"),
    ("EMBEDDING_API_BASE", "", "Embedding API Base URL (为空时使用 LLM 的 API Base)"),
]

for key, value, desc in configs:
    config = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    if config:
        config.config_value = value
        config.description = desc
    else:
        config = SystemConfig(config_key=key, config_value=value, description=desc)
        db.add(config)

db.commit()
db.close()
```

---

### 配置项说明

| 配置项 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `EMBEDDING_MODEL` | Embedding 模型名称 | `text-embedding-ada-002` | `BAAI/bge-small-zh-v1.5` |
| `EMBEDDING_API_KEY` | Embedding API Key | `""` (空,使用 LLM 的 Key) | `sk-proj-xxxxx` |
| `EMBEDDING_API_BASE` | Embedding API Base URL | `""` (空,使用 LLM 的 Base) | `https://api.openai.com/v1` |

**重要**: 
- 如果 `EMBEDDING_API_KEY` 为空,自动使用 `OPENAI_API_KEY`
- 如果 `EMBEDDING_API_BASE` 为空,自动使用 `OPENAI_API_BASE`

---

### 实现细节

#### 1. 后端配置 (`backend/app/core/config.py`)

```python
class Settings(BaseSettings):
    # OpenAI/LLM
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    MODEL_NAME: str = "gpt-4"
    
    # Embedding 模型配置(支持单独的 API)
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_API_KEY: str = ""  # 为空时使用 OPENAI_API_KEY
    EMBEDDING_API_BASE: str = ""  # 为空时使用 OPENAI_API_BASE
```

#### 2. RAG 服务初始化 (`backend/app/services/rag_service.py`)

```python
def __init__(self, db: Session = None):
    # 从数据库读取配置
    embedding_api_key = settings.EMBEDDING_API_KEY
    embedding_api_base = settings.EMBEDDING_API_BASE
    
    if db:
        configs = db.query(SystemConfig).filter(
            SystemConfig.config_key.in_([
                'EMBEDDING_MODEL', 'EMBEDDING_API_KEY', 'EMBEDDING_API_BASE'
            ])
        ).all()
        
        config_dict = {c.config_key: c.config_value for c in configs}
        embedding_api_key = config_dict.get('EMBEDDING_API_KEY', embedding_api_key)
        embedding_api_base = config_dict.get('EMBEDDING_API_BASE', embedding_api_base)
    
    # 如果 Embedding 配置为空,使用 LLM 的配置
    if not embedding_api_key:
        embedding_api_key = api_key
    if not embedding_api_base:
        embedding_api_base = api_base
    
    # 初始化 Embeddings
    self.embeddings = OpenAIEmbeddings(
        model=embedding_model,
        api_key=embedding_api_key,
        base_url=embedding_api_base if embedding_api_base else None
    )
```

#### 3. API 接口 (`backend/app/api/v1/endpoints/system_config.py`)

```python
@router.get("/embedding")
def get_embedding_config(db: Session = Depends(get_db)):
    """获取 Embedding 模型配置"""
    embedding_model_config = get_or_create_config(db, "EMBEDDING_MODEL", ...)
    embedding_api_key_config = get_or_create_config(db, "EMBEDDING_API_KEY", ...)
    embedding_api_base_config = get_or_create_config(db, "EMBEDDING_API_BASE", ...)
    
    return {
        "embedding_model": embedding_model_config.config_value,
        "embedding_api_key": masked_key,
        "embedding_api_key_full": api_key,
        "embedding_api_base": embedding_api_base_config.config_value
    }

@router.put("/embedding")
def update_embedding_config(config: EmbeddingConfigUpdate, db: Session = Depends(get_db)):
    """更新 Embedding 模型配置"""
    # 更新数据库
    # 更新 .env 文件
    # 更新运行时配置
    return {"message": "Embedding 模型配置更新成功"}
```

#### 4. 前端配置页面 (`frontend/src/pages/Settings.tsx`)

```tsx
<TabPane tab="Embedding 配置" key="embedding">
  <Form form={embeddingForm} onFinish={onSaveEmbedding}>
    <Form.Item name="embedding_model" label="Embedding 模型名称">
      <Input placeholder="text-embedding-ada-002" />
    </Form.Item>
    <Form.Item name="embedding_api_key" label="Embedding API Key">
      <Input.Password placeholder="为空时使用 LLM 的 API Key" />
    </Form.Item>
    <Form.Item name="embedding_api_base" label="Embedding API Base URL">
      <Input placeholder="为空时使用 LLM 的 API Base" />
    </Form.Item>
    <Button type="primary" htmlType="submit">保存配置</Button>
  </Form>
</TabPane>
```

---

### 测试结果

```bash
$ python -m scripts.test_embedding_config

============================================================
测试 Embedding 配置功能
============================================================

1️⃣  当前配置:

LLM 配置:
  OPENAI_API_KEY: ms-1edea540-3aa5-475...
  OPENAI_API_BASE: https://api-inference.modelscope.cn/v1
  MODEL_NAME: deepseek-ai/DeepSeek-V3.1

Embedding 配置:
  EMBEDDING_MODEL: BAAI/bge-small-zh-v1.5
  EMBEDDING_API_KEY: (空,使用 LLM 的 API Key)
  EMBEDDING_API_BASE: (空,使用 LLM 的 API Base)

2️⃣  测试 RAG 服务初始化:
[INFO] RAG 服务配置:
  LLM API Base: https://api-inference.modelscope.cn/v1
  LLM Model: deepseek-ai/DeepSeek-V3.1
  Embedding API Base: https://api-inference.modelscope.cn/v1
  Embedding Model: BAAI/bge-small-zh-v1.5

✅ RAG 服务初始化成功!

3️⃣  验证配置逻辑:
  ✅ Embedding API Key 为空,使用 LLM 的 API Key
  ✅ Embedding API Base 为空,使用 LLM 的 API Base
```

---

### 相关文件

- ✅ `backend/app/core/config.py` - 添加 Embedding 配置项
- ✅ `backend/app/schemas/system_config.py` - 添加 EmbeddingConfigUpdate Schema
- ✅ `backend/app/api/v1/endpoints/system_config.py` - 添加 GET/PUT /embedding 接口
- ✅ `backend/app/services/rag_service.py` - 支持单独的 Embedding 配置
- ✅ `frontend/src/services/api.ts` - 添加前端 API 接口
- ✅ `frontend/src/pages/Settings.tsx` - 添加 Embedding 配置 Tab
- ✅ `backend/scripts/test_embedding_config.py` - 测试脚本

---

### 下一步

1. **刷新浏览器**: 按 F5 刷新页面
2. **访问系统管理**: 点击左侧菜单 "系统管理"
3. **查看 Embedding 配置**: 点击 "Embedding 配置" Tab
4. **配置 Embedding**: 根据需要填写配置
5. **保存并重启**: 保存配置后重启后端服务

所有功能已实现! 🎉 现在可以为 Embedding 模型配置单独的 API 和 Key 了! 🎊
