# 故障排除指南

## 常见问题和解决方案

### 1. psycopg2-binary 编译错误

**错误信息**:
```
error: Microsoft Visual C++ 14.0 or greater is required.
ERROR: Failed building wheel for psycopg2-binary
```

**原因**: Python 3.13 没有 psycopg2-binary 的预编译包

**解决方案**: 
项目已升级到 `psycopg` v3，请重新安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

详见: [PYTHON_313_COMPATIBILITY.md](./PYTHON_313_COMPATIBILITY.md)

---

### 2. CORS_ORIGINS 配置错误

**错误信息**:
```
pydantic_settings.exceptions.SettingsError: error parsing value for field "CORS_ORIGINS" from source "DotEnvSettingsSource"
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
```

**原因**: `.env` 文件中 CORS_ORIGINS 使用了 JSON 格式

**解决方案**:
编辑 `backend/.env` 文件，修改 CORS_ORIGINS 格式：

❌ **错误格式**:
```env
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
```

✅ **正确格式**:
```env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

### 3. SQLAlchemy 与 Python 3.13 不兼容

**错误信息**:
```
AssertionError: Class <class 'sqlalchemy.sql.elements.SQLCoreOperations'> directly inherits TypingOnly but has additional attributes
```

**原因**: SQLAlchemy 2.0.25 不支持 Python 3.13

**解决方案**:
项目已升级到 SQLAlchemy 2.0.36+，请重新安装依赖：
```bash
cd backend
pip install -r requirements.txt --upgrade
```

---

### 3.5. ModuleNotFoundError: No module named 'psycopg2'

**错误信息**:
```
ModuleNotFoundError: No module named 'psycopg2'
File "D:\caseDemo1\backend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\psycopg2.py", line 696, in import_dbapi
    import psycopg2
```

**原因**: `.env` 文件中的 DATABASE_URL 格式错误，SQLAlchemy 尝试使用 psycopg2 而不是 psycopg

**解决方案**:

#### 方法 1: 使用自动修复脚本（推荐）
```bash
cd backend
python fix_env.py
```

#### 方法 2: 手动修复
编辑 `backend/.env` 文件，修改 DATABASE_URL：

❌ **错误格式**:
```env
DATABASE_URL=postgresql://testcase:testcase123@localhost:5432/test_case_db
```

✅ **正确格式**:
```env
DATABASE_URL=postgresql+psycopg://testcase:testcase123@localhost:5432/test_case_db
```

**关键点**: 必须使用 `postgresql+psycopg://` 而不是 `postgresql://`

#### 验证修复
```bash
cd backend
python check_config.py
```

---

### 3.6. email-validator 未安装

**错误信息**:
```
ModuleNotFoundError: No module named 'email_validator'
ImportError: email-validator is not installed, run `pip install 'pydantic[email]'`
```

**原因**: Pydantic 的 EmailStr 类型需要 email-validator 包

**解决方案**:
项目已添加 email-validator 到 requirements.txt，请重新安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

或单独安装：
```bash
pip install email-validator==2.1.0
```

---

### 3.7. 循环导入错误

**错误信息**:
```
ImportError: cannot import name 'User' from partially initialized module 'app.models.user' (most likely due to a circular import)
```

**原因**: `app.db.base` 和模型文件之间存在循环导入

**解决方案**:
项目已修复循环导入问题。如果您修改了代码导致此问题，请确保：

1. `app/db/base.py` 使用延迟导入：
```python
def import_models():
    """Import all models to ensure they are registered with SQLAlchemy"""
    from app.models.user import User
    from app.models.requirement import Requirement
    from app.models.test_point import TestPoint
    from app.models.test_case import TestCase
    return User, Requirement, TestPoint, TestCase
```

2. `main.py` 在启动时调用 `import_models()`：
```python
from app.db.base import Base, import_models

@asynccontextmanager
async def lifespan(app: FastAPI):
    import_models()  # 导入所有模型
    Base.metadata.create_all(bind=engine)
    yield
```

---

### 4. 数据库连接失败

**错误信息**:
```
sqlalchemy.exc.OperationalError: (psycopg.OperationalError) connection failed
```

**可能原因**:
1. Docker 容器未启动
2. 数据库 URL 格式错误
3. 数据库凭据错误

**解决方案**:

#### 检查 Docker 容器
```bash
docker-compose ps
```

如果容器未运行：
```bash
docker-compose up -d
```

#### 检查数据库 URL 格式
编辑 `backend/.env`，确保使用正确格式：
```env
DATABASE_URL=postgresql+psycopg://testcase:testcase123@localhost:5432/test_case_db
```

注意：
- ✅ 必须使用 `postgresql+psycopg://`
- ❌ 不要使用 `postgresql://`

#### 检查数据库凭据
默认凭据（在 docker-compose.yml 中定义）：
- 用户名: `testcase`
- 密码: `testcase123`
- 数据库: `test_case_db`
- 端口: `5432`

---

### 5. .env 文件不存在

**错误信息**:
```
配置文件未找到或配置错误
```

**解决方案**:

#### 方法 1: 使用脚本（推荐）
```bash
setup-env.bat
```

#### 方法 2: 手动创建
```bash
cd backend
copy .env.example .env
```

然后编辑 `.env` 文件，配置必要参数：
```env
OPENAI_API_KEY=sk-your-api-key-here
DATABASE_URL=postgresql+psycopg://testcase:testcase123@localhost:5432/test_case_db
```

---

### 6. OpenAI API Key 未配置

**错误信息**:
```
openai.error.AuthenticationError: No API key provided
```

**解决方案**:
编辑 `backend/.env` 文件，添加您的 OpenAI API Key：
```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

---

### 7. 端口被占用

**错误信息**:
```
OSError: [WinError 10048] 通常每个套接字地址(协议/网络地址/端口)只允许使用一次
```

**可能原因**:
- 后端端口 8000 被占用
- 前端端口 5173 被占用
- 数据库端口 5432 被占用

**解决方案**:

#### 查找占用端口的进程
```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :5173
netstat -ano | findstr :5432
```

#### 终止进程
```bash
# Windows (使用进程 ID)
taskkill /PID <进程ID> /F
```

#### 或修改端口
编辑配置文件使用其他端口。

---

### 8. Milvus 连接失败

**错误信息**:
```
MilvusException: <MilvusException: (code=1, message=Fail connecting to server)>
```

**解决方案**:

#### 检查 Milvus 容器
```bash
docker-compose ps
```

确保以下容器都在运行：
- casedemo1-milvus-standalone-1
- casedemo1-milvus-etcd-1
- casedemo1-milvus-minio-1

#### 重启 Milvus
```bash
docker-compose restart milvus-standalone
```

#### 检查配置
编辑 `backend/.env`：
```env
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

---

### 9. 前端依赖安装失败

**错误信息**:
```
npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree
```

**解决方案**:

#### 清理缓存
```bash
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

#### 使用 --legacy-peer-deps
```bash
npm install --legacy-peer-deps
```

---

### 10. 虚拟环境问题

**问题**: 依赖安装到全局 Python 而不是虚拟环境

**解决方案**:

#### 创建虚拟环境
```bash
cd backend
python -m venv .venv
```

#### 激活虚拟环境
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

#### 安装依赖
```bash
pip install -r requirements.txt
```

---

### 11. 登录后没有反应 / 401 Unauthorized

**现象**:
- 点击登录按钮后没有跳转
- 后端日志显示: `POST /api/v1/auth/login 200 OK` 但 `GET /api/v1/users/me 401 Unauthorized`

**原因**:
前端在获取用户信息时，token 还没有被正确传递到请求头

**解决方案**:
项目已修复此问题。如果仍有问题：

1. **清除浏览器缓存和 LocalStorage**:
   - 打开浏览器开发者工具 (F12)
   - Application → Local Storage → 删除所有项
   - 刷新页面

2. **检查前端代码**:
   确保 `Login.tsx` 中正确传递 token:
   ```typescript
   const userResponse = await authAPI.getMe(access_token)
   ```

3. **创建测试用户**:
   ```bash
   create-test-user.bat
   ```

   使用以下信息登录:
   - 用户名: `admin`
   - 密码: `admin123`

4. **检查后端日志**:
   查看是否有其他错误信息

---

### 12. 上传需求文档后一直超时 / 处理失败

**现象**:
- 上传文档后状态一直显示"处理中"
- 页面加载超时
- 后端没有错误日志

**可能原因**:
1. OpenAI API Key 未配置或无效
2. 文档解析失败
3. AI 服务调用超时
4. 网络连接问题

**解决方案**:

#### 1. 检查 OpenAI API Key 配置

编辑 `backend/.env` 文件:
```env
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4
```

**重要**:
- 如果没有 OpenAI API Key，系统会使用模拟数据
- 确保 API Key 有效且有足够的配额

#### 2. 测试文档处理功能

```bash
cd backend
python test_document_processing.py
```

这将测试:
- 文档解析功能
- AI 测试点提取
- 显示详细的错误信息

#### 3. 测试 OpenAI API 连接

```bash
cd backend
python test_document_processing.py api
```

这将验证:
- API Key 是否有效
- 网络连接是否正常
- API Base URL 是否正确

#### 4. 查看后端日志

后端会输出详细的处理日志:
```
[INFO] 开始处理需求文档 ID: 1
[INFO] 解析文档: ./uploads/xxx.txt
[INFO] 文档解析成功，文本长度: 1234
[INFO] 调用 AI 服务提取测试点...
[INFO] OpenAI API 响应成功
[INFO] 成功解析 5 个测试点
[INFO] 需求处理完成 ID: 1
```

如果看到错误:
```
[ERROR] 处理需求失败 ID: 1, 错误: ...
```

根据错误信息进行相应处理。

#### 5. 使用模拟数据测试

如果暂时无法配置 OpenAI API:
1. 不配置 `OPENAI_API_KEY` 或设置为空
2. 系统会自动使用模拟数据
3. 可以测试其他功能

#### 6. 检查文档格式

支持的文档格式:
- ✅ DOCX (Microsoft Word)
- ✅ PDF
- ✅ TXT (UTF-8 或 GBK 编码)
- ✅ XLS / XLSX (Excel)

确保文档:
- 文件大小 < 10MB
- 格式正确，没有损坏
- 包含可读取的文本内容

#### 7. 增加超时时间

如果文档很大，可能需要更长的处理时间。

编辑 `frontend/src/services/api.ts`:
```typescript
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,  // 增加到 60 秒
})
```

---

### 13. 需求列表点击"查看"没有反应

**现象**:
- 点击需求列表中的"查看"按钮没有任何反应
- 无法查看需求详情和测试点

**原因**:
前端"查看"按钮没有绑定点击事件

**解决方案**:
已修复此问题。现在点击"查看"按钮会：
1. 打开右侧抽屉显示需求详情
2. 显示需求的基本信息（标题、描述、文件信息、状态等）
3. 显示该需求下的所有测试点列表

**功能说明**:
- 需求详情包括：标题、描述、文件名、文件类型、文件大小、状态、创建时间
- 测试点列表包括：ID、标题、描述、分类、优先级
- 支持分页显示测试点

---

### 14. 需求列表操作列功能说明

**操作列包含的功能**:

#### 1. 查看
- 点击"查看"按钮打开需求详情抽屉
- 显示需求的完整信息
- 显示该需求下的所有测试点

#### 2. 生成测试点
- 点击"生成测试点"按钮重新生成测试点
- 会删除该需求下的所有旧测试点
- 使用 AI 重新分析需求文档生成新的测试点
- 适用场景：
  - 首次上传文档时未配置 OpenAI API Key
  - 需求文档已更新，需要重新分析
  - 对现有测试点不满意，需要重新生成

**使用方法**:
1. 点击"生成测试点"按钮
2. 确认提示框（会删除现有测试点）
3. 系统后台重新生成测试点
4. 通过 WebSocket 实时通知生成进度

**注意事项**:
- 重新生成会删除该需求下的所有旧测试点及其关联的测试用例
- 确保已配置 OpenAI API Key，否则会使用模拟数据
- 生成过程在后台进行，可以继续使用其他功能

#### 3. 删除
- 删除需求及其关联的所有测试点和测试用例
- 删除上传的文档文件
- 操作不可恢复，请谨慎使用

---

### 15. 测试点和测试用例查看功能

**测试点查看功能**:

1. **查看测试点详情**:
   - 在"用例管理"页面的"测试点"标签页
   - 点击测试点行的"查看"按钮
   - 右侧抽屉显示测试点详情

2. **显示内容**:
   - 测试点基本信息（ID、标题、描述、分类、优先级）
   - 用例数量统计
   - 创建时间
   - 用户反馈（如果有）
   - 该测试点生成的所有测试用例列表

3. **查看生成的用例**:
   - 在测试点详情抽屉中
   - 滚动到"生成的测试用例"部分
   - 查看该测试点下的所有用例
   - 点击用例的"查看详情"按钮可以查看用例完整信息

**测试用例查看功能**:

1. **查看测试用例详情**:
   - 在"用例管理"页面的"测试用例"标签页
   - 点击测试用例行的"查看"按钮
   - 右侧抽屉显示测试用例详情

2. **显示内容**:
   - 测试用例基本信息（ID、标题、描述）
   - 优先级和测试类型
   - 前置条件（完整内容）
   - 测试步骤（完整内容）
   - 预期结果（完整内容）
   - 创建时间

3. **功能特性**:
   - 支持多行文本显示
   - 保留原始格式（换行、缩进等）
   - 优先级和类型使用彩色标签显示

**操作列功能总结**:

**测试点操作列**:
- 👁️ **查看**: 查看测试点详情和生成的用例
- ⚡ **生成用例**: 为测试点生成测试用例
- 🗑️ **删除**: 删除测试点及其关联用例

**测试用例操作列**:
- 👁️ **查看**: 查看测试用例详情
- ✏️ **编辑**: 编辑测试用例内容
- 🗑️ **删除**: 删除测试用例

---

### 16. 系统配置管理权限问题

**问题**: 打开系统管理页面提示 "The user doesn't have enough privileges"

**原因**: 当前登录用户不是超级管理员

**解决方案 1: 使用脚本设置超级管理员（推荐）**

运行设置超级管理员脚本:
```bash
set-superuser.bat
```

脚本会：
1. 显示当前所有用户列表
2. 提示输入要设置为超级管理员的用户名
3. 自动设置该用户为超级管理员

**解决方案 2: 手动在数据库中设置**

1. 连接到 PostgreSQL 数据库:
   ```bash
   psql -U testcase -d test_case_db
   ```

2. 查看所有用户:
   ```sql
   SELECT username, email, is_superuser FROM users;
   ```

3. 设置用户为超级管理员:
   ```sql
   UPDATE users SET is_superuser = true WHERE username = 'admin';
   ```

4. 验证设置:
   ```sql
   SELECT username, is_superuser FROM users WHERE username = 'admin';
   ```

**解决方案 3: 使用测试用户**

如果使用了 `create-test-user.bat` 创建的测试用户，该用户默认已经是超级管理员:
- 用户名: `admin`
- 密码: `admin123`

**注意事项**:
- ✅ 设置完成后需要**重新登录**才能获取新权限
- ⚠️ 超级管理员拥有所有权限，请谨慎授予
- 🔒 建议只设置少数必要的用户为超级管理员

---

### 17. 系统配置保存和使用

**问题**: 需要修改 Milvus 或模型配置

**解决方案 1: 通过 Web 界面配置（推荐）**

1. **访问配置页面**:
   - 使用管理员账号登录
   - 进入"系统管理"页面

2. **配置 Milvus**:
   - 在"Milvus 配置"卡片中填写 Host 和 Port
   - 点击"保存配置"
   - 重启后端生效

3. **配置模型**:
   - 在"模型配置"卡片中填写 API Key、API Base URL 和模型名称
   - 点击"保存配置"
   - 部分配置立即生效，完全生效需要重启后端

4. **首次使用需要创建数据库表**:
   ```bash
   create-system-config-table.bat
   ```

**解决方案 2: 手动编辑 .env 文件**

1. 编辑 `backend/.env` 文件
2. 修改相应配置项
3. 重启后端

**常见配置示例**:

**OpenAI 官方**:
```env
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4
```

**ModelScope**:
```env
OPENAI_API_KEY=ms-...
OPENAI_API_BASE=https://api-inference.modelscope.cn/v1/chat/completions
MODEL_NAME=deepseek-ai/DeepSeek-V3.1
```

**Milvus**:
```env
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

**注意事项**:
- ✅ Web 界面配置会同时更新数据库和 .env 文件
- ⚠️ 只有超级管理员可以访问配置管理
- 🔄 配置修改后建议重启后端确保完全生效

---

### 18. 测试用例搜索和筛选

**功能**: 在测试用例列表中快速查找和筛选用例

**使用方法**:

1. **按测试点筛选**:
   - 在"测试用例"标签页
   - 使用"筛选测试点"下拉框
   - 选择特定测试点
   - 只显示该测试点下的用例

2. **关键词搜索**:
   - 在搜索框输入关键词
   - 按回车或点击搜索图标
   - 系统会在以下字段中搜索：
     - 标题
     - 描述
     - 前置条件
     - 预期结果

3. **组合使用**:
   - 可以同时使用测试点筛选和关键词搜索
   - 例如：先选择测试点，再搜索关键词

4. **清除筛选**:
   - 点击"清除筛选"按钮
   - 或清空搜索框
   - 或清除测试点选择

**使用场景**:

- 📋 **查找特定功能的用例**: 使用测试点筛选
- 🔍 **搜索包含特定关键词的用例**: 使用关键词搜索
- 🎯 **精确定位**: 组合使用筛选和搜索
- 📊 **查看统计**: 查看筛选后的用例数量

**提示**:
- ✅ 搜索不区分大小写
- ✅ 支持部分匹配
- ✅ 实时显示筛选结果数量
- ✅ 分页功能自动适配筛选结果

---

## 诊断工具

### 环境检查脚本
运行完整的环境检查：
```bash
check-setup.bat
```

这将检查：
- Python 版本
- Node.js 版本
- Docker 状态
- .env 文件
- 数据库容器
- 依赖安装

### 手动检查清单

- [ ] Python 3.10+ 已安装
- [ ] Node.js 18+ 已安装
- [ ] Docker Desktop 正在运行
- [ ] `backend/.env` 文件存在
- [ ] `OPENAI_API_KEY` 已配置
- [ ] `DATABASE_URL` 格式正确 (`postgresql+psycopg://`)
- [ ] `CORS_ORIGINS` 格式正确 (逗号分隔)
- [ ] Docker 容器正在运行 (`docker-compose ps`)
- [ ] 后端依赖已安装
- [ ] 前端依赖已安装

---

## 获取帮助

如果以上方案都无法解决您的问题：

1. **查看详细文档**:
   - [README.md](./readme.md) - 项目说明
   - [QUICK_START.md](./QUICK_START.md) - 快速启动
   - [README_SETUP.md](./README_SETUP.md) - 详细配置
   - [PYTHON_313_COMPATIBILITY.md](./PYTHON_313_COMPATIBILITY.md) - Python 3.13 兼容性

2. **查看日志**:
   ```bash
   # 后端日志
   查看终端输出
   
   # Docker 日志
   docker-compose logs
   docker-compose logs postgres
   docker-compose logs milvus-standalone
   ```

3. **重新开始**:
   ```bash
   # 停止所有服务
   docker-compose down -v
   
   # 删除虚拟环境
   rm -rf backend/.venv backend/venv
   
   # 删除前端依赖
   rm -rf frontend/node_modules
   
   # 重新开始安装
   setup-env.bat
   docker-compose up -d
   install-backend.bat
   install-frontend.bat
   ```

---

## 版本兼容性

### 推荐版本

| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.10 - 3.13 | 推荐 3.11 或 3.13 |
| Node.js | 18+ | 推荐 LTS 版本 |
| Docker | 最新版 | Docker Desktop |
| PostgreSQL | 15 | 通过 Docker |
| Milvus | 2.3+ | 通过 Docker |

### 已测试环境

- ✅ Windows 11 + Python 3.13 + Node.js 20
- ✅ Windows 10 + Python 3.11 + Node.js 18
- ⏳ macOS (待测试)
- ⏳ Linux (待测试)

