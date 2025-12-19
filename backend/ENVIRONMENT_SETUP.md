# 环境配置说明

## 配置文件

在 `backend/` 目录下创建 `.env` 文件，配置以下环境变量。

## 配置项说明

### 1. 数据库配置

```bash
# SQLite（开发环境）
DATABASE_URL=sqlite:///./test_cases.db

# PostgreSQL（生产环境推荐）
DATABASE_URL=postgresql://user:password@localhost/dbname

# MySQL
DATABASE_URL=mysql+pymysql://user:password@localhost/dbname
```

### 2. JWT 认证配置

```bash
# JWT 密钥（生产环境请使用强密钥）
SECRET_KEY=your-secret-key-here-change-in-production

# 加密算法
ALGORITHM=HS256

# Token 过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

生成强密钥的方法：
```bash
# 使用 Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 使用 OpenSSL
openssl rand -hex 32
```

### 3. AI 服务配置

#### OpenAI API

```bash
# API 密钥
OPENAI_API_KEY=your-openai-api-key

# API 地址（使用代理或第三方服务）
OPENAI_API_BASE=https://api.siliconflow.cn/v1

# 模型名称
MODEL_NAME=deepseek-coder
```

#### Embedding 配置

```bash
# API 密钥
EMBEDDING_API_KEY=your-embedding-api-key

# API 地址
EMBEDDING_API_BASE=https://api.siliconflow.cn/v1

# 模型名称
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
```

#### AI 请求配置

```bash
# 最大重试次数
AI_MAX_RETRIES=3

# 重试间隔（秒）
AI_RETRY_INTERVAL=2.0

# 请求超时时间（秒）
AI_REQUEST_TIMEOUT=180
```

### 4. 自动化测试平台配置 ⭐

**这是新增的配置项，用于集成自动化测试平台。**

```bash
# 自动化测试平台 API 地址
AUTOMATION_PLATFORM_API_BASE=http://your-automation-platform.com
```

**配置示例：**

```bash
# 本地部署
AUTOMATION_PLATFORM_API_BASE=http://192.168.1.100:8080

# 远程服务
AUTOMATION_PLATFORM_API_BASE=https://automation.example.com

# 带端口号
AUTOMATION_PLATFORM_API_BASE=http://test-platform.local:9000
```

**注意事项：**
- URL 末尾不要加斜杠 `/`
- 确保后端服务可以访问该地址
- 如果未配置，自动化用例生成功能将不可用

### 5. 应用配置

```bash
# 项目名称
PROJECT_NAME=测试用例管理系统

# 调试模式（生产环境设为 False）
DEBUG=False
```

### 6. CORS 配置

```bash
# 允许的前端地址（JSON 数组格式）
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

## 完整配置示例

创建 `backend/.env` 文件：

```bash
# ========================================
# 数据库配置
# ========================================
DATABASE_URL=sqlite:///./test_cases.db

# ========================================
# JWT 配置
# ========================================
SECRET_KEY=your-secret-key-change-this-in-production-use-strong-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ========================================
# AI 服务配置
# ========================================
# OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_BASE=https://api.siliconflow.cn/v1
MODEL_NAME=deepseek-coder

# Embedding
EMBEDDING_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EMBEDDING_API_BASE=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5

# AI 请求配置
AI_MAX_RETRIES=3
AI_RETRY_INTERVAL=2.0
AI_REQUEST_TIMEOUT=180

# ========================================
# 自动化测试平台配置 ⭐ 新增
# ========================================
AUTOMATION_PLATFORM_API_BASE=http://192.168.1.100:8080

# ========================================
# 应用配置
# ========================================
PROJECT_NAME=测试用例管理系统
DEBUG=False

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

## 配置验证

### 1. 检查配置是否加载

启动后端服务后，查看日志：

```bash
cd backend
python main.py
```

应该看到类似输出：
```
[INFO] Starting application...
[INFO] Database URL: sqlite:///./test_cases.db
[INFO] AI Service initialized with model: deepseek-coder
[INFO] Automation platform: http://192.168.1.100:8080
```

### 2. 测试自动化平台连接

使用 Python 脚本测试：

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

base_url = os.getenv('AUTOMATION_PLATFORM_API_BASE')
if not base_url:
    print("❌ AUTOMATION_PLATFORM_API_BASE 未配置")
else:
    print(f"✅ 配置地址: {base_url}")
    try:
        # 测试连接（根据实际 API 调整）
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ 连接成功: {response.status_code}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
```

### 3. 使用配置检查工具

```bash
cd backend
python -c "
from app.core.config import settings
print('Database:', settings.DATABASE_URL)
print('OpenAI Base:', settings.OPENAI_API_BASE)
print('Automation Platform:', settings.AUTOMATION_PLATFORM_API_BASE or 'Not configured')
"
```

## 安全建议

### 生产环境

1. **使用强密钥**
   ```bash
   # 生成 256-bit 密钥
   openssl rand -hex 32
   ```

2. **保护 .env 文件**
   ```bash
   # 设置文件权限（Linux/Mac）
   chmod 600 .env
   ```

3. **不要提交到 Git**
   - 确保 `.env` 在 `.gitignore` 中
   - 使用 `.env.example` 作为模板

4. **使用环境变量管理工具**
   - Docker Secrets
   - Kubernetes ConfigMap/Secrets
   - AWS Secrets Manager
   - Azure Key Vault

### 密钥轮换

定期更新密钥：

```bash
# 1. 生成新密钥
NEW_KEY=$(openssl rand -hex 32)

# 2. 更新 .env
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$NEW_KEY/" .env

# 3. 重启服务
systemctl restart backend
```

## 故障排除

### 问题1: 配置未生效

**症状**：修改了 `.env` 但配置未更新

**解决**：
1. 确保 `.env` 文件在正确的位置（`backend/` 目录）
2. 重启后端服务
3. 检查是否有语法错误（等号两边不要有空格）

### 问题2: 数据库连接失败

**症状**：`OperationalError: unable to open database file`

**解决**：
1. 检查数据库路径是否正确
2. 确保目录有写权限
3. 对于 SQLite，确保目录存在

### 问题3: AI API 调用失败

**症状**：`Request timed out` 或 `Authentication failed`

**解决**：
1. 检查 API 密钥是否正确
2. 检查 API 地址是否可访问
3. 增加 `AI_REQUEST_TIMEOUT` 值
4. 检查网络连接和防火墙设置

### 问题4: 自动化平台连接失败

**症状**：`自动化测试平台服务未配置或不可用`

**解决**：
1. 检查 `AUTOMATION_PLATFORM_API_BASE` 是否配置
2. 测试网络连接：`curl http://your-platform.com`
3. 检查 URL 格式是否正确（不要末尾斜杠）
4. 确保后端可以访问该地址（检查防火墙、代理设置）

## 相关文档

- [自动化平台集成说明](../AUTOMATION_PLATFORM_INTEGRATION.md)
- [快速开始指南](../AUTOMATION_QUICK_START.md)
- [部署指南](./DEPLOY_SCENARIO.md)


