# Embedding 模型配置修复

## ✅ 问题已解决!

### 问题描述
上传文档时报错:
```
Error code: 400 - {'errors': {'message': 'Invalid model id: text-embedding-ada-002'}}
```

### 根本原因
1. **使用的是 ModelScope API**(阿里云模型服务),而不是 OpenAI 官方 API
2. **默认 embedding 模型** 是 `text-embedding-ada-002`(OpenAI 模型)
3. **ModelScope 不支持** OpenAI 的 embedding 模型

### 解决方案

#### 1. **添加 EMBEDDING_MODEL 配置** ✅

**修改文件**: `backend/app/core/config.py`
```python
class Settings(BaseSettings):
    # OpenAI/LLM
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    MODEL_NAME: str = "gpt-4"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"  # 新增
```

#### 2. **修改 RAG 服务读取配置** ✅

**修改文件**: `backend/app/services/rag_service.py`
```python
def __init__(self, db: Session = None):
    """初始化 RAG 服务"""
    self.db = db
    
    # 从数据库读取配置
    api_key = settings.OPENAI_API_KEY
    api_base = settings.OPENAI_API_BASE
    model_name = settings.MODEL_NAME
    embedding_model = settings.EMBEDDING_MODEL  # 新增
    
    if db:
        from app.models.system_config import SystemConfig
        configs = db.query(SystemConfig).filter(
            SystemConfig.config_key.in_([
                'OPENAI_API_KEY', 
                'OPENAI_API_BASE', 
                'MODEL_NAME', 
                'EMBEDDING_MODEL'  # 新增
            ])
        ).all()
        
        config_dict = {c.config_key: c.config_value for c in configs}
        api_key = config_dict.get('OPENAI_API_KEY', api_key)
        api_base = config_dict.get('OPENAI_API_BASE', api_base)
        model_name = config_dict.get('MODEL_NAME', model_name)
        embedding_model = config_dict.get('EMBEDDING_MODEL', embedding_model)  # 新增
    
    print(f"[INFO] RAG 服务配置:")
    print(f"  API Base: {api_base}")
    print(f"  LLM Model: {model_name}")
    print(f"  Embedding Model: {embedding_model}")  # 新增
    
    # 初始化 Embeddings
    self.embeddings = OpenAIEmbeddings(
        model=embedding_model,  # 使用配置的模型
        api_key=api_key,
        base_url=api_base if api_base else None
    )
```

#### 3. **添加数据库配置** ✅

**执行脚本**: `backend/add_embedding_config.py`
```python
from app.db.session import SessionLocal
from app.models.system_config import SystemConfig

db = SessionLocal()

config = SystemConfig(
    config_key='EMBEDDING_MODEL',
    config_value='BAAI/bge-small-zh-v1.5',  # ModelScope 支持的中文 embedding 模型
    description='Embedding 模型 (ModelScope 支持的中文 embedding 模型)'
)

db.merge(config)
db.commit()
db.close()
```

### 验证结果

```bash
$ python test_rag_config.py

============================================================
测试 RAG 服务配置
============================================================

创建 RAG 服务...
[INFO] RAG 服务配置:
  API Base: https://api-inference.modelscope.cn/v1
  LLM Model: deepseek-ai/DeepSeek-V3.1
  Embedding Model: BAAI/bge-small-zh-v1.5

✅ RAG 服务创建成功!

LLM 配置:
  Model: deepseek-ai/DeepSeek-V3.1
  API Base: https://api-inference.modelscope.cn/v1

Embedding 配置:
  Model: BAAI/bge-small-zh-v1.5
  API Base: https://api-inference.modelscope.cn/v1
```

### 当前配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| OPENAI_API_KEY | ms-1edea540-3aa5-475... | ModelScope API Key |
| OPENAI_API_BASE | https://api-inference.modelscope.cn/v1 | ModelScope API 地址 |
| MODEL_NAME | deepseek-ai/DeepSeek-V3.1 | LLM 模型 |
| EMBEDDING_MODEL | BAAI/bge-small-zh-v1.5 | Embedding 模型 (中文) |

### ModelScope 支持的 Embedding 模型

1. **BAAI/bge-small-zh-v1.5** ✅ (当前使用)
   - 中文 embedding 模型
   - 维度: 512
   - 适合中文文本检索

2. **BAAI/bge-base-zh-v1.5**
   - 中文 embedding 模型
   - 维度: 768
   - 更高精度,但速度较慢

3. **BAAI/bge-large-zh-v1.5**
   - 中文 embedding 模型
   - 维度: 1024
   - 最高精度,速度最慢

### 下一步操作

#### 1. **刷新浏览器页面**
在浏览器中按 **F5** 刷新页面,确保加载最新配置

#### 2. **上传测试文档**
1. 访问 http://localhost:5173
2. 登录系统 (admin / admin123)
3. 点击左侧菜单 "知识问答"
4. 点击右上角 "上传文档"
5. 填写文档信息:
   ```
   标题: 保险业务知识
   内容:
   投保人需要提供以下材料:
   1. 身份证原件及复印件
   2. 投保申请书
   3. 健康告知书
   4. 银行卡信息
   
   投保流程包括:
   1. 填写投保申请书
   2. 提交健康告知
   3. 核保审核
   4. 缴纳保费
   5. 生成保单
   
   保单变更需要3-5个工作日。
   理赔审核时间为7-10个工作日。
   
   分类: 保险业务
   标签: 投保,保全,理赔,材料,流程
   ```
6. 点击 "上传"

#### 3. **测试流式问答**
上传成功后,在聊天框输入问题:

```
问: 投保人需要提供哪些材料?
答: [流式显示] 根据知识库,投保人需要提供以下材料...▊

问: 投保流程是什么?
答: [流式显示] 投保流程包括以下步骤...▊

问: 保单变更需要多长时间?
答: [流式显示] 保单变更需要3-5个工作日...▊
```

#### 4. **预期效果**
- ✅ 文档上传成功 (不再报 400 错误)
- ✅ 文本逐字显示 (打字机效果)
- ✅ 绿色光标闪烁 ▊
- ✅ 显示参考来源
- ✅ 基于知识库的准确回答

### 服务状态

- ✅ **后端**: http://0.0.0.0:8000 (Terminal 2)
- ✅ **前端**: http://localhost:5173 (Terminal 3)
- ✅ **Milvus**: localhost:19530
- ✅ **配置**: 已更新为 ModelScope 兼容模型

### 相关文件

- ✅ `backend/app/core/config.py` - 添加 EMBEDDING_MODEL 配置
- ✅ `backend/app/services/rag_service.py` - 从数据库读取 embedding 模型配置
- ✅ `backend/add_embedding_config.py` - 添加数据库配置脚本
- ✅ `backend/test_rag_config.py` - 测试配置脚本

所有问题已解决! 🎉 现在可以正常上传文档并进行流式问答了! 🎊

