# 智能测试用例平台 - 安装指南

## 项目概述

这是一个基于 AI 的智能测试用例生成平台，专为保险行业设计。用户可以上传需求文档，系统会自动识别测试点并生成相关测试用例。

## 技术栈

### 后端
- FastAPI - Web 框架
- LangGraph 1.0.2 - AI 工作流编排
- LangChain 1.0.2 - LLM 集成
- PostgreSQL - 关系数据库
- Milvus - 向量数据库
- SQLAlchemy - ORM
- WebSocket - 实时通知

### 前端
- React 18
- TypeScript
- Vite
- Ant Design 5
- Zustand - 状态管理
- Axios - HTTP 客户端

## 环境要求

- Python 3.10+ (支持 Python 3.13)
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15
- Milvus 2.3+

> **注意**: 如果使用 Python 3.13，项目已升级到 `psycopg` (v3) 以避免编译问题。详见 [PYTHON_313_COMPATIBILITY.md](./PYTHON_313_COMPATIBILITY.md)

## 快速开始

### 1. 启动数据库服务

使用 Docker Compose 启动 PostgreSQL 和 Milvus：

```bash
docker-compose up -d
```

等待所有服务启动完成（约 1-2 分钟）。

### 2. 后端设置

#### 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 配置环境变量

复制环境变量模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下关键参数：

```env
# 数据库配置（使用 psycopg 驱动）
DATABASE_URL=postgresql+psycopg://testcase:testcase123@localhost:5432/test_case_db

# Milvus 配置
MILVUS_HOST=localhost
MILVUS_PORT=19530

# OpenAI API 配置（必须配置）
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4

# JWT 密钥（生产环境请修改）
SECRET_KEY=your-secret-key-change-this-in-production
```

> **重要**: 数据库 URL 必须使用 `postgresql+psycopg://` 格式（不是 `postgresql://`）

#### 启动后端服务

```bash
python main.py
```

后端服务将在 `http://localhost:8000` 启动。

访问 API 文档：`http://localhost:8000/docs`

### 3. 前端设置

#### 安装依赖

```bash
cd frontend
npm install
```

#### 启动前端开发服务器

```bash
npm run dev
```

前端服务将在 `http://localhost:5173` 启动。

## 使用说明

### 1. 注册/登录

首次使用需要注册账号：
- 访问 `http://localhost:5173`
- 点击"注册"标签
- 填写用户名、邮箱和密码
- 注册成功后使用账号登录

### 2. 上传需求文档

- 进入"需求管理"页面
- 点击"上传需求"按钮
- 填写需求标题和描述
- 选择需求文档（支持 DOCX、PDF、TXT、XLS、XLSX）
- 点击上传

系统会自动：
1. 解析文档内容
2. 使用 AI 识别测试点
3. 通过 WebSocket 实时通知生成进度

### 3. 查看和管理测试点

- 进入"用例管理"页面
- 在"测试点"标签页查看生成的测试点
- 可以筛选、编辑或删除测试点
- 点击"生成用例"为测试点生成详细的测试用例

### 4. 查看测试用例

- 在"用例管理"页面的"测试用例"标签页
- 查看所有生成的测试用例
- 可以编辑、删除测试用例

### 5. 系统配置

- 进入"系统管理"页面
- 配置 Milvus 连接参数
- 配置 AI 模型参数（API Key、模型名称等）

## 功能特性

### 已实现功能

✅ 用户注册和登录  
✅ 需求文档上传（支持多种格式）  
✅ AI 自动识别测试点  
✅ AI 生成测试用例  
✅ WebSocket 实时通知  
✅ 测试点和用例管理  
✅ 首页数据统计  
✅ 系统配置管理  

### 核心流程

1. **需求上传** → 文档解析 → AI 分析 → 生成测试点
2. **测试点** → 用户审核/修改 → 提交反馈 → 重新生成（可选）
3. **测试点** → 选择生成用例 → AI 生成详细测试用例
4. **实时通知** → WebSocket 推送生成进度和结果

## 项目结构

```
.
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── db/             # 数据库配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # 业务服务
│   ├── main.py             # 应用入口
│   └── requirements.txt    # Python 依赖
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # React 组件
│   │   ├── pages/          # 页面组件
│   │   ├── services/       # API 服务
│   │   └── stores/         # 状态管理
│   └── package.json        # Node 依赖
├── docker-compose.yml      # Docker 配置
└── readme.md              # 项目说明
```

## 常见问题

### 1. 数据库连接失败

确保 Docker 容器正在运行：
```bash
docker-compose ps
```

### 2. AI 生成失败

检查 `.env` 文件中的 OpenAI API Key 是否正确配置。

### 3. WebSocket 连接失败

确保后端服务正在运行，并且前端配置的 WebSocket URL 正确。

### 4. 文档解析失败

确保上传的文档格式正确，文件未损坏。

## 开发说明

### 后端开发

- 使用 FastAPI 的自动文档：`http://localhost:8000/docs`
- 数据库迁移使用 Alembic（如需要）
- 遵循 RESTful API 设计规范

### 前端开发

- 使用 TypeScript 进行类型检查
- 遵循 React Hooks 最佳实践
- 使用 Ant Design 组件库

## 生产部署

### 后端部署

1. 设置生产环境变量
2. 使用 Gunicorn 或 Uvicorn 部署
3. 配置 Nginx 反向代理
4. 启用 HTTPS

### 前端部署

1. 构建生产版本：`npm run build`
2. 部署 `dist` 目录到静态服务器
3. 配置 Nginx 或 CDN

## 许可证

MIT License

## 联系方式

如有问题，请联系开发团队。

