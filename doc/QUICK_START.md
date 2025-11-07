# 快速启动指南

## ⚠️ 重要提示

**首次使用必读**:
1. ✅ 需要创建**超级管理员账号**才能访问系统配置
2. ✅ 需要配置 **AI 模型 API Key** 才能使用 AI 功能
3. ✅ 配置修改后需要**重启后端**才能生效

## 5 分钟快速启动

### 前置条件

确保已安装：
- ✅ Python 3.10+ (推荐 3.11 或 3.13)
- ✅ Node.js 18+
- ✅ Docker Desktop

> **遇到问题？** 查看 [故障排除指南](./TROUBLESHOOTING.md)

### 步骤 1：启动数据库（1 分钟）

打开终端，在项目根目录执行：

```bash
docker-compose up -d
```

等待所有容器启动完成。

### 步骤 2：配置后端（1 分钟）

1. 复制环境变量文件：
```bash
cd backend
copy .env.example .env
```

2. 编辑 `backend/.env` 文件，**必须配置 OpenAI API Key**：
```env
OPENAI_API_KEY=你的API密钥
DATABASE_URL=postgresql+psycopg://testcase:testcase123@localhost:5432/test_case_db
```

其他配置可以保持默认。

> **重要**: 数据库 URL 必须使用 `postgresql+psycopg://` 格式（Python 3.13 兼容）

### 步骤 3：安装后端依赖（1 分钟）

双击运行：
```
install-backend.bat
```

或手动执行：
```bash
cd backend
pip install -r requirements.txt
```

### 步骤 4：安装前端依赖（1 分钟）

双击运行：
```
install-frontend.bat
```

或手动执行：
```bash
cd frontend
npm install
```

### 步骤 5：启动服务（1 分钟）

**启动后端**（新终端窗口）：
```
双击 start-backend.bat
```

或手动执行：
```bash
cd backend
python main.py
```

**启动前端**（新终端窗口）：
```
双击 start-frontend.bat
```

或手动执行：
```bash
cd frontend
npm run dev
```

### 步骤 6：访问系统

打开浏览器访问：
```
http://localhost:5173
```

## 首次使用

### 1. 创建管理员账号

**方法 1: 使用脚本创建（推荐）**

双击运行：
```
create-test-user.bat
```

这将创建一个超级管理员账号：
- **用户名**: `admin`
- **密码**: `admin123`
- **邮箱**: `admin@example.com`

**方法 2: 注册后设置为超级管理员**

如果已经注册了账号，运行：
```
set-superuser.bat
```

按提示输入用户名，将该用户设置为超级管理员。

### 2. 登录系统

使用管理员账号登录：
- 用户名: `admin`
- 密码: `admin123`

### 3. 配置系统（重要！）

**创建配置表**:
```
create-system-config-table.bat
```

**配置 AI 模型**:
1. 登录后点击左侧菜单的"系统管理"
2. 在"模型配置"卡片中填写：
   - **API Key**: 你的 API 密钥
   - **API Base URL**: API 地址
   - **模型名称**: 模型名称

**示例配置（ModelScope）**:
```
API Key: ms-xxxxxxxxxxxxx
API Base URL: https://api-inference.modelscope.cn/v1/chat/completions
模型名称: deepseek-ai/DeepSeek-V3.1
```

3. 点击"保存配置"
4. **重启后端**使配置生效

> **注意**: 如果不配置 API Key，系统会使用模拟数据，无法真正使用 AI 功能

### 4. 上传需求文档
- 进入"需求管理"
- 点击"上传需求"
- 填写标题和描述
- 选择文档文件（支持 DOCX、PDF、TXT、XLS、XLSX）
- 点击上传

### 4. 查看测试点
- 等待系统处理（会收到通知）
- 进入"用例管理" → "测试点"
- 查看 AI 生成的测试点

### 5. 生成测试用例
- 在测试点列表中点击"生成用例"
- 等待生成完成（会收到通知）
- 切换到"测试用例"标签查看

## 常见问题

### Q1: Docker 容器启动失败？
**A:** 确保 Docker Desktop 正在运行，端口 5432 和 19530 未被占用。

### Q2: 后端启动失败？
**A:** 检查：
1. Python 版本是否 3.10+
2. 依赖是否安装完成
3. `.env` 文件是否配置正确
4. Docker 容器是否正在运行

### Q3: 前端启动失败？
**A:** 检查：
1. Node.js 版本是否 18+
2. 依赖是否安装完成（`npm install`）
3. 端口 5173 是否被占用

### Q4: AI 生成失败？
**A:** 检查：
1. OpenAI API Key 是否正确配置
2. API Key 是否有效
3. 网络是否可以访问 OpenAI API

### Q5: WebSocket 连接失败？
**A:** 确保后端服务正在运行，刷新页面重新连接。

## 服务地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:5173 | React 应用 |
| 后端 | http://localhost:8000 | FastAPI 服务 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| PostgreSQL | localhost:5432 | 数据库 |
| Milvus | localhost:19530 | 向量数据库 |

## 默认配置

### 数据库
- 用户名: `testcase`
- 密码: `testcase123`
- 数据库: `test_case_db`

### Milvus
- Host: `localhost`
- Port: `19530`

## 停止服务

### 停止前后端
在运行的终端窗口按 `Ctrl + C`

### 停止数据库
```bash
docker-compose down
```

### 完全清理（包括数据）
```bash
docker-compose down -v
```

## 下一步

- 📖 阅读 [README.md](./readme.md) 了解详细功能
- 📚 阅读 [README_SETUP.md](./README_SETUP.md) 了解详细配置
- 🔍 阅读 [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) 了解项目结构

## 技术支持

遇到问题？
1. 检查本文档的"常见问题"部分
2. 查看终端的错误信息
3. 检查 Docker 容器状态：`docker-compose ps`
4. 查看容器日志：`docker-compose logs`

祝使用愉快！🎉

