# CLAUDE.md

这个文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

智能测试用例平台是一个基于 AI 的自动化测试用例生成系统,专为保险行业设计。用户上传需求文档后,系统使用 LangGraph 和 LangChain 自动识别测试点并生成详细的测试用例。

**技术栈**:
- 后端: FastAPI + LangChain 1.0+ + LangGraph 1.0+ + PostgreSQL + Milvus
- 前端: React 18 + TypeScript + Vite + Ant Design 5 + Zustand
- AI: OpenAI API + 硅基流动嵌入 (BAAI/bge-large-zh-v1.5)

## 核心命令

### 环境启动

```bash
# 启动数据库服务 (PostgreSQL + Milvus + etcd + MinIO)
docker-compose up -d

# 检查容器状态
docker-compose ps
```

### 后端开发

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器 (热重载,监听 0.0.0.0:8000)
python -m scripts.main

# 或使用批处理脚本 (Windows)
..\bat\start-backend.bat
```

**重要**: 后端使用 Python 3.10+,数据库驱动为 `psycopg` (不是 psycopg2)。数据库 URL 格式必须是 `postgresql+psycopg://`。

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器 (http://localhost:5173)
npm run dev

# 构建生产版本
npm run build

# TypeScript 类型检查 + 构建
tsc && vite build

# ESLint 检查
npm run lint
```

### 测试

项目暂无自动化测试框架。测试脚本集中在 `backend/scripts/` 目录,用于手动验证功能:

```bash
cd backend

# 功能测试
python -m scripts.test_*.py

# 用户管理
python -m scripts.create_test_user     # 创建测试用户
python -m scripts.set_superuser        # 设置超级管理员

# 审批功能测试
python -m scripts.test_approval
```

### 调试和故障排查

```bash
# 查看Docker容器日志
docker-compose logs -f postgres    # PostgreSQL 日志
docker-compose logs -f milvus      # Milvus 日志

# 检查数据库连接
docker exec -it test_case_postgres psql -U testcase -d test_case_db

# 查看后端日志（开发服务器会直接输出到控制台）
# 生产环境日志位置取决于部署配置
```

## 核心架构

### AI 工作流 (LangGraph)

**测试点生成流程** (`backend/app/services/ai_service.py`):
1. **需求文档上传** → 文档解析 (`document_parser.py`)
2. **文档向量化** → Milvus 嵌入存储 (`document_embedding_service.py`)
3. **LangGraph 状态机** → 调用 LLM 分析需求
4. **测试点识别** → 保存到 PostgreSQL
5. **WebSocket 通知** → 实时推送进度 (`websocket_service.py`)

**测试用例生成流程**:
1. 用户选择测试点
2. 从 Milvus 检索需求上下文 (RAG)
3. LLM 生成测试用例 (前置条件、步骤、预期结果)
4. 保存到数据库并通知前端

### 自动化平台集成

**核心服务**: `backend/app/services/automation_service.py`

**主要流程** (`create_case_with_fields`):
1. `get_scene_cases(scene_id)` - 获取场景用例列表
2. `select_best_case_by_ai()` - AI选择最匹配模板 (180秒超时保护)
3. `get_case_detail(usercase_id)` - 获取模板详情（含header/body）
4. `generate_case_body_by_ai()` - AI生成测试数据
5. `create_case_and_body()` - 创建用例和明细

**超时保护机制**:
- AI 选择用例时使用 `ThreadPoolExecutor` + 180 秒超时
- 超时后自动降级使用第一个可用用例
- 优化 Prompt 长度减少 token 使用
- 如果只有 1 个用例则跳过 AI 调用

**关键API端点**:
- `POST /ai/case/createCaseAndBody` - 创建用例和明细
- `GET /ai/case/queryCaseBody/{id}` - 获取用例详情
- `GET /ai/case/queryBySceneId/{sceneId}` - 获取场景用例

**caseDefine数据结构**:
```python
{
    "header": [{"rowName", "row", "type", "flag"}],  # 字段定义
    "body": [{"casedesc", "var": {...}}]             # 测试数据
}
```

### 模型配置系统

系统支持**多模型配置管理** (支持为单个配置添加多个模型):
- 数据库表: `model_configs` (优先级最高)
- 环境变量: `.env` 文件 (回退方案)
- 前端界面: `/model-configs` 页面管理模型

**多模型配置特性**:
- `model_name` 字段存储 JSON 数组格式 (如 `["gpt-4", "gpt-3.5-turbo"]`)
- `selected_model` 字段指定当前使用的模型
- 前端提供下拉选择器,支持预设模型列表和自定义输入
- 支持按提供商分组显示 (OpenAI、智谱AI、通义千问等)

**AI 服务初始化逻辑**:
1. 如果传入 `model_config_id`,使用指定模型配置
2. 否则查询 `is_default=True` 的模型配置
3. 如果数据库查询失败,回退到环境变量 (`OPENAI_API_KEY`, `MODEL_NAME`)
4. 使用 `selected_model` 字段的值作为实际调用的模型

### 向量数据库 (Milvus)

- **文档嵌入**: 需求文档切分后使用硅基流动 API 生成向量,写入 Milvus
- **RAG 检索**: 生成测试用例时,从 Milvus 检索相关需求上下文
- **配置参数**: `DOCUMENT_CHUNK_SIZE=500`, `DOCUMENT_CHUNK_OVERLAP=100`

**关键服务**:
- `milvus_service.py` - Milvus 连接和操作
- `document_embedding_service.py` - 文档向量化
- `rag_service.py` - RAG 检索和问答

### WebSocket 实时通知

- 端点: `ws://localhost:8000/api/v1/ws/{client_id}`
- 认证: 使用 JWT token (`?token=xxx`)
- 消息类型: `test_points_generated`, `test_case_generated`, `knowledge_base_completed`

**前端实现**:
- `frontend/src/stores/websocketStore.ts` - WebSocket 连接管理
- 自动重连机制,状态同步到 Zustand store

### 数据模型关系

```
User (用户)
  ├── Requirement (需求文档)
  │     ├── TestPoint (测试点)
  │     │     └── TestCase (测试用例)
  │     └── KnowledgeBase (知识库向量数据)
  └── ModelConfig (模型配置)
```

**核心模型**:
- `backend/app/models/requirement.py` - 需求文档
- `backend/app/models/test_point.py` - 测试点
- `backend/app/models/test_case.py` - 测试用例
- `backend/app/models/model_config.py` - 模型配置
- `backend/app/models/knowledge_base.py` - 知识库

### API 路由结构

所有 API 路由在 `backend/app/api/v1/endpoints/`:
- `auth.py` - 用户认证 (登录/注册)
- `requirements.py` - 需求管理 (上传/列表/删除)
- `test_points.py` - 测试点管理 (生成/反馈/删除)
- `test_cases.py` - 测试用例管理 (生成/编辑/删除)
- `dashboard.py` - 数据统计
- `model_config.py` - 模型配置 CRUD
- `knowledge_base.py` - 知识库管理和 RAG 聊天
- `websocket.py` - WebSocket 连接
- `system_config.py` - Milvus 系统配置

## 环境配置

### 必须配置的环境变量

创建 `backend/.env` 文件 (参考 `.env.example`):

```env
# OpenAI/LLM API (必须)
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4

# 硅基流动嵌入 API (必须)
EMBEDDING_API_KEY=your_EMBEDDING_API_KEY_here
EMBEDDING_API_BASE=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5

# 数据库 (使用 psycopg 驱动)
DATABASE_URL=postgresql+psycopg://testcase:testcase123@localhost:5432/test_case_db

# Milvus 向量数据库
MILVUS_HOST=localhost
MILVUS_PORT=19530

# 自动化测试平台 API
AUTOMATION_PLATFORM_API_BASE=http://localhost:8087
```

**注意**:
- 如果使用 Python 3.13,必须使用 `postgresql+psycopg://` 格式
- API Key 默认不应提交到 Git,通过环境变量或数据库配置管理
- 自动化平台API地址支持从数据库(`system_config`表)或环境变量读取

## 常见开发场景

### 添加新的 API 端点

1. 在 `backend/app/api/v1/endpoints/` 创建或编辑文件
2. 定义 Pydantic schema (`backend/app/schemas/`)
3. 在 `backend/app/api/v1/__init__.py` 注册路由
4. 前端对应在 `frontend/src/services/` 添加 API 调用

### 修改 AI 提示词

- 测试点生成提示: `backend/app/services/ai_service.py` → `generate_test_points()` 方法
- 测试用例生成提示: `ai_service.py` → `generate_test_cases()` 方法
- 提示词模板使用 `ChatPromptTemplate.from_messages()`

### 修改文档解析逻辑

编辑 `backend/app/services/document_parser.py`:
- 支持格式: DOCX, PDF, TXT, XLS, XLSX
- 增强解析逻辑建议在 `parse_document()` 方法中添加

### 前端状态管理

使用 Zustand 管理全局状态 (`frontend/src/stores/`):
- `authStore.ts` - 用户认证状态
- `websocketStore.ts` - WebSocket 连接
- 状态直接在组件中通过 `useAuthStore()` 等 hooks 访问

### 数据库迁移

项目使用 Alembic 进行迁移,但当前主要通过 SQLAlchemy 自动创建表 (`main.py` 中的 `Base.metadata.create_all()`)。

**手动迁移脚本**:

```bash
cd backend

# 创建表
python -m scripts.create_system_config_table
python -m scripts.create_model_configs_table

# 数据迁移
python -m scripts.migrate_model_name_to_array    # 迁移 model_name 为 JSON 数组
python -m scripts.add_selected_model_field       # 添加 selected_model 字段
```

**重要迁移**:
- `migrate_model_name_to_array.py` - 将 model_name 从字符串转为 JSON 数组格式
- `add_selected_model_field.py` - 为模型配置添加 selected_model 字段

## 最近功能更新

### 1. 多模型选择功能 (2026-02-03)
- 模型配置支持添加多个模型 (JSON 数组格式)
- 前端提供预设模型列表下拉选择
- 支持主流 AI 模型: OpenAI GPT、智谱 GLM、通义千问、DeepSeek、Claude 等
- 详细文档: `doc/MODEL_NAME_SELECTOR.md`

### 2. AI 选择超时优化 (2026-02-03)
- 添加 180 秒超时保护机制,防止 AI 调用卡死
- 超时后自动降级使用第一个可用用例
- 优化 Prompt 长度,减少约 70% token 使用
- 详细文档: `doc/AI_SELECTION_TIMEOUT_FIX.md`

### 3. 审批工作流 (2025-11-07)
- 测试点和测试用例支持完整审批流程
- 三种状态: 待审批 (pending)、已通过 (approved)、已拒绝 (rejected)
- 支持审批意见和审批历史记录
- 详细文档: `doc/审批功能说明.md`

## 重要注意事项

1. **LangChain 版本**: 项目使用 LangChain 1.0+,API 参数为 `api_key` 和 `base_url` (不是旧版的 `openai_api_key`)
2. **数据库驱动**: 必须使用 `psycopg` (不是 psycopg2),URL 格式为 `postgresql+psycopg://`
3. **CORS 配置**: 前端默认运行在 5173 端口,后端 CORS 已配置允许
4. **文件上传**: 文件存储在 `backend/uploads/` 目录,通过静态文件服务访问
5. **WebSocket 认证**: 必须在 URL 参数中传递 JWT token
6. **模型配置优先级**: 数据库配置 > 环境变量
7. **AI 超时控制**: 自动化用例生成时 AI 调用有 180 秒超时保护,避免卡死
8. **多模型配置**: model_name 使用 JSON 数组格式,selected_model 指定实际使用的模型

## 批处理脚本 (Windows)

位于 `bat/` 目录的便捷脚本:
- `install-backend.bat` / `install-frontend.bat` - 安装依赖
- `start-backend.bat` / `start-frontend.bat` - 启动服务
- `setup-env.bat` - 环境配置向导
- `check-setup.bat` - 环境检查
- `create-test-user.bat` - 创建测试用户
- `set-superuser.bat` - 设置超级管理员

## 参考文档

详细文档位于 `doc/` 目录:

**核心文档**:
- `QUICK_START.md` - 5 分钟快速启动
- `ARCHITECTURE.md` - 系统架构设计
- `FEATURES.md` - 功能详细说明
- `TROUBLESHOOTING.md` - 问题排查指南
- `MIGRATION_GUIDE.md` - LangChain 1.0 迁移指南

**功能文档**:
- `MODEL_NAME_SELECTOR.md` - 模型名称下拉选择功能
- `MULTI_MODEL_CONFIG.md` - 多模型配置详细说明
- `MULTI_MODEL_QUICK_START.md` - 多模型快速入门
- `AI_SELECTION_TIMEOUT_FIX.md` - AI 选择超时问题修复
- `审批功能说明.md` - 测试点/用例审批流程
