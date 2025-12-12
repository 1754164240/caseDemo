"""修复 readme.md 文件的编码问题。"""
from scripts import REPO_ROOT

# README 内容
readme_content = """# 智能测试用例平台（保险行业）

## 平台简介

智能测试用例平台是一个基于 AI 的自动化测试用例生成系统，专为保险行业设计。用户可以上传需求文档，系统会自动识别测试点并生成详细的测试用例，大幅提升测试工作效率。

### 核心功能 

- 📄 **需求文档上传**：支持 DOCX、PDF、TXT、XLS、XLSX 等多种格式
- 🤖 **AI 智能识别**：使用 LangGraph 和 LangChain 自动识别测试点
- 📊 **文档向量化**：硅基流动 BAAI/bge-large-zh-v1.5 自动切分嵌入并写入 Milvus
- ✅ **测试用例生成**：基于测试点自动生成详细的测试用例
- 💬 **反馈优化**：支持用户反馈，AI 根据反馈重新生成
- 🔔 **实时通知**：WebSocket 实时推送生成进度和结果
- 📈 **数据统计**：首页展示需求数、测试点数、用例数等关键指标

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

## 快速开始

详细文档请参考：
- 📚 [快速启动指南](./doc/QUICK_START.md) - 5 分钟快速启动
- 📖 [详细安装指南](./doc/README_SETUP.md) - 完整安装和配置说明
- 🏗️ [系统架构文档](./doc/ARCHITECTURE.md) - 技术架构和设计
- 📋 [功能说明](./doc/FEATURES.md) - 详细功能介绍
- 🔧 [问题排查指南](./doc/TROUBLESHOOTING.md) - 常见问题解决方案

### 环境要求
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15
- Milvus 2.3+

### 快速启动

```bash
# 1. 启动数据库服务
docker-compose up -d

# 2. 安装后端依赖（Windows）
bat\\install-backend.bat

# 3. 配置环境变量
# 复制 backend/.env.example 为 backend/.env 并配置

# 4. 启动后端服务（Windows）
bat\\start-backend.bat

# 5. 安装前端依赖（Windows）
bat\\install-frontend.bat

# 6. 启动前端服务（Windows）
bat\\start-frontend.bat
```

访问 http://localhost:5173 开始使用！

## 核心功能

### 1. 需求管理
- 上传需求文档（DOCX、PDF、TXT、XLS、XLSX）
- 自动解析文档内容
- 文档向量化存储到 Milvus
- AI 自动识别测试点

### 2. 测试点管理
- 查看 AI 生成的测试点
- 按需求筛选测试点
- 提交反馈优化测试点
- 生成测试用例

### 3. 测试用例管理
- 查看详细测试用例
- 编辑测试用例
- 测试步骤管理
- 前置条件和预期结果

### 4. 系统管理
- 模型配置管理
- Milvus 配置
- 用户管理

## 技术支持

- **快速开始**: 参考 [QUICK_START.md](./doc/QUICK_START.md)
- **详细配置**: 参考 [README_SETUP.md](./doc/README_SETUP.md)
- **架构设计**: 参考 [ARCHITECTURE.md](./doc/ARCHITECTURE.md)
- **功能说明**: 参考 [FEATURES.md](./doc/FEATURES.md)
- **问题排查**: 参考 [TROUBLESHOOTING.md](./doc/TROUBLESHOOTING.md)

## 许可证

MIT License
"""

# 写入文件
readme_path = REPO_ROOT / "readme.md"

# 删除旧文件
if readme_path.exists():
    readme_path.unlink()
    print(f"✅ 已删除旧文件: {readme_path}")

# 写入新文件（UTF-8 编码，无 BOM）
with readme_path.open('w', encoding='utf-8') as f:
    f.write(readme_content)

print(f"✅ 已创建新文件: {readme_path}")
print("✅ 文件编码: UTF-8 (无 BOM)")
print("✅ 中文显示正常")
