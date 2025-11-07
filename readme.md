# 智能测试用例平台（保险行业）

## 平台简介

智能测试用例平台是一个基于 AI 的自动化测试用例生成系统，专为保险行业设计。用户可以上传需求文档，系统会自动识别测试点并生成详细的测试用例，大幅提升测试工作效率。

### 核心功能 

- 📄 **需求文档上传**：支持 DOCX、PDF、TXT、XLS、XLSX 等多种格式
- 🤖 **AI 智能识别**：使用 LangGraph 和 LangChain 自动识别测试点
- ✨ **测试用例生成**：基于测试点自动生成详细的测试用例
- 💬 **反馈优化**：支持用户反馈，AI 根据反馈重新生成
- 🔔 **实时通知**：WebSocket 实时推送生成进度和结果
- 📊 **数据统计**：首页展示需求数、测试点数、用例数等关键指标

## 技术架构

### 后端技术栈
- **FastAPI** - 现代化的 Python Web 框架
- **LangGraph 1.0.2** - AI 工作流编排框架
- **LangChain 1.0.2** - LLM 应用开发框架
- **OpenAI 1.x** - OpenAI API 客户端
- **PostgreSQL** - 关系型数据库
- **Milvus** - 向量数据库（知识库）
- **SQLAlchemy** - Python ORM
- **WebSocket** - 实时通信

### 前端技术栈
- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Ant Design 5** - UI 组件库
- **Zustand** - 状态管理
- **Axios** - HTTP 客户端

## 业务模块

### 1. 首页（Dashboard）
- 展示需求总数
- 展示测试点总数
- 展示测试用例总数
- 显示当前使用的 AI 模型
- 展示最近上传的需求列表

### 2. 需求管理
- 上传需求文档（支持 DOCX、PDF、TXT、XLS、XLSX）
- 需求列表展示（标题、状态、文件类型、测试点数、用例数）
- 需求详情查看
- 需求文档预览
- 需求删除

### 3. 用例管理
- **测试点管理**
  - 查看所有测试点
  - 按需求筛选测试点
  - 测试点详情（标题、描述、分类、优先级）
  - 提交反馈意见
  - 生成测试用例
  - 删除测试点

- **测试用例管理**
  - 查看所有测试用例
  - 测试用例详情（标题、描述、前置条件、测试步骤、预期结果）
  - 编辑测试用例
  - 删除测试用例

### 4. 系统管理
- **Milvus 配置**：配置向量数据库连接参数
- **模型配置**：配置 AI 模型（API Key、模型名称、API Base）
- **用户管理**：管理系统用户（开发中）

### 5. 实时通知
- 测试点生成完成通知（WebSocket）
- 测试用例生成完成通知（WebSocket）
- 进度更新实时推送

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15
- Milvus 2.3+

### 安装步骤

#### 1. 启动数据库服务

```bash
docker-compose up -d
```

#### 2. 安装后端依赖

Windows:
```bash
bat\install-backend.bat
```

或手动安装:
```bash
cd backend
pip install -r requirements.txt
```

#### 3. 配置环境变量

复制 `backend/.env.example` 为 `backend/.env`，并配置：

```env
# 必须配置 OpenAI API Key
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4

# 数据库配置（使用 psycopg 驱动）
DATABASE_URL=postgresql+psycopg://testcase:testcase123@localhost:5432/test_case_db

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

> **注意**: 如果使用 Python 3.13，请确保数据库 URL 使用 `postgresql+psycopg://` 格式

#### 4. 启动后端服务

Windows:
```bash
bat\start-backend.bat
```

或手动启动:
```bash
cd backend
python main.py
```

后端服务：http://localhost:8000
API 文档：http://localhost:8000/docs

#### 5. 安装前端依赖

Windows:
```bash
bat\install-frontend.bat
```

或手动安装:
```bash
cd frontend
npm install
```

#### 6. 启动前端服务

Windows:
```bash
bat\start-frontend.bat
```

或手动启动:
```bash
cd frontend
npm run dev
```

前端服务：http://localhost:5173

## 使用指南

### 1. 注册和登录
- 访问 http://localhost:5173
- 点击"注册"创建账号
- 使用账号登录系统

### 2. 上传需求文档
- 进入"需求管理"页面
- 点击"上传需求"
- 填写需求信息并选择文档
- 系统自动解析并生成测试点

### 3. 管理测试点
- 进入"用例管理" → "测试点"
- 查看 AI 生成的测试点
- 可以提交反馈让 AI 重新生成
- 点击"生成用例"创建测试用例

### 4. 查看测试用例
- 进入"用例管理" → "测试用例"
- 查看详细的测试用例
- 可以编辑和删除用例

## 项目结构

```
caseDemo1/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/               # API 路由
│   │   │   └── v1/
│   │   │       └── endpoints/ # API 端点
│   │   ├── core/              # 核心配置
│   │   ├── db/                # 数据库配置
│   │   ├── models/            # 数据模型
│   │   ├── schemas/           # Pydantic Schemas
│   │   └── services/          # 业务服务
│   │       ├── ai_service.py      # AI 生成服务
│   │       ├── document_parser.py # 文档解析
│   │       ├── milvus_service.py  # 向量数据库
│   │       └── websocket_service.py # WebSocket
│   ├── main.py                # 应用入口
│   ├── requirements.txt       # Python 依赖
│   └── .env.example          # 环境变量模板
├── frontend/                  # 前端代码
│   ├── src/
│   │   ├── components/       # React 组件
│   │   ├── pages/            # 页面组件
│   │   ├── services/         # API 服务
│   │   └── stores/           # 状态管理
│   ├── package.json          # Node 依赖
│   └── vite.config.ts        # Vite 配置
├── docker-compose.yml        # Docker 配置
├── README_SETUP.md          # 详细安装指南
└── readme.md                # 项目说明（本文件）
```

## 核心流程

### 测试点生成流程
1. 用户上传需求文档
2. 后端解析文档内容
3. LangGraph 工作流启动
4. LangChain 调用 LLM 分析需求
5. 识别测试点并保存到数据库
6. WebSocket 通知前端生成完成

### 测试用例生成流程
1. 用户选择测试点
2. 点击"生成用例"
3. 后端获取测试点和需求上下文
4. LangChain 调用 LLM 生成测试用例
5. 保存测试用例到数据库
6. WebSocket 通知前端生成完成

## API 文档

启动后端服务后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发说明

### 后端开发
- 遵循 FastAPI 最佳实践
- 使用 SQLAlchemy ORM
- 异步处理耗时任务
- WebSocket 实时通知

### 前端开发
- TypeScript 类型安全
- React Hooks
- Ant Design 组件
- Zustand 状态管理

## 常见问题

**Q: 如何配置 AI 模型？**
A: 在 `backend/.env` 文件中配置 `OPENAI_API_KEY`、`OPENAI_API_BASE` 和 `MODEL_NAME`。

**Q: 支持哪些文档格式？**
A: 支持 DOCX、PDF、TXT、XLS、XLSX 格式。

**Q: 如何查看生成进度？**
A: 系统通过 WebSocket 实时推送生成进度，会在页面右上角显示通知。

**Q: 数据库连接失败怎么办？**
A: 确保 Docker 容器正在运行：`docker-compose ps`

## 更新日志

### v1.1.0 (2025-11-06)
- 🚀 **LangChain 升级**: 0.1.0 → 0.3.13
- 🚀 **LangGraph 升级**: 0.1.0 → 0.2.62
- ✨ 新增 OpenAI SDK 1.x 支持
- 🔧 API 参数更新（api_key, base_url）
- 📚 完善的迁移文档

详见 [CHANGELOG.md](./CHANGELOG.md) 和 [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)

### v1.0.0 (2025-11-05)
- ✅ 完整的前后端实现
- ✅ AI 测试点识别
- ✅ AI 测试用例生成
- ✅ WebSocket 实时通知
- ✅ 多格式文档支持
- ✅ 用户认证和授权
- ✅ 数据统计和展示

## 许可证

MIT License

## 文档导航

- 📖 [README.md](./readme.md) - 项目说明（本文件）
- 🚀 [QUICK_START.md](./QUICK_START.md) - 5 分钟快速启动指南
- 📚 [README_SETUP.md](./README_SETUP.md) - 详细安装和配置指南
- 🏗️ [ARCHITECTURE.md](./ARCHITECTURE.md) - 系统架构文档
- 📋 [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) - 项目总览和文件清单

## 技术支持

- **快速开始**: 参考 [QUICK_START.md](./QUICK_START.md)
- **详细配置**: 参考 [README_SETUP.md](./README_SETUP.md)
- **架构设计**: 参考 [ARCHITECTURE.md](./ARCHITECTURE.md)
- **项目结构**: 参考 [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)