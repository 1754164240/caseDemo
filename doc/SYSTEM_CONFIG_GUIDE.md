# 系统配置管理指南

## 概述

系统配置管理功能允许管理员通过 Web 界面配置系统参数，包括 Milvus 向量数据库和 AI 模型配置。配置会同时保存到数据库和 `.env` 文件中。

## 功能特性

- ✅ **Web 界面配置**: 无需手动编辑配置文件
- 💾 **双重保存**: 同时保存到数据库和 .env 文件
- 🔒 **权限控制**: 只有超级管理员可以访问
- 🔐 **安全显示**: API Key 自动脱敏显示
- 📝 **配置说明**: 提供详细的配置示例和说明

## 首次使用

### 1. 创建数据库表

首次使用前需要创建 `system_configs` 表：

```bash
create-system-config-table.bat
```

或者手动运行：

```bash
cd backend
.venv\Scripts\activate
python create_system_config_table.py
```

### 2. 确保有超级管理员账号

配置管理功能只对超级管理员开放。如果还没有超级管理员账号，需要在数据库中手动设置：

```sql
UPDATE users SET is_superuser = true WHERE username = 'admin';
```

或者使用测试用户创建脚本创建的 `admin` 账号（默认已是超级管理员）。

## 使用方法

### 访问配置页面

1. 使用超级管理员账号登录系统
2. 点击左侧菜单的"系统管理"
3. 进入配置页面

### 配置 Milvus

**Milvus 配置**用于连接向量数据库，存储和检索测试用例的向量表示。

**配置项**:
- **Milvus Host**: Milvus 服务器地址
  - 本地部署: `localhost`
  - 远程服务器: IP 地址或域名
- **Milvus Port**: Milvus 服务器端口
  - 默认端口: `19530`

**操作步骤**:
1. 在"Milvus 配置"卡片中填写 Host 和 Port
2. 点击"保存配置"按钮
3. 等待保存成功提示
4. **重启后端**使配置完全生效

### 配置 AI 模型

**模型配置**用于设置 AI 服务的 API 信息，支持 OpenAI、ModelScope 等兼容 OpenAI API 的服务。

**配置项**:
- **API Key**: API 密钥
- **API Base URL**: API 基础地址
- **模型名称**: 使用的模型

**操作步骤**:
1. 在"模型配置"卡片中填写配置信息
2. 点击"保存配置"按钮
3. 等待保存成功提示
4. 部分配置立即生效，**建议重启后端**确保完全生效

## 配置示例

### OpenAI 官方 API

```
API Key: sk-proj-xxxxxxxxxxxxx
API Base URL: https://api.openai.com/v1
模型名称: gpt-4
```

或者使用 GPT-3.5:
```
API Key: sk-proj-xxxxxxxxxxxxx
API Base URL: https://api.openai.com/v1
模型名称: gpt-3.5-turbo
```

### ModelScope API

```
API Key: ms-1edea540-3aa5-4757-be16-11e2ddb5abbe
API Base URL: https://api-inference.modelscope.cn/v1/chat/completions
模型名称: deepseek-ai/DeepSeek-V3.1
```

其他 ModelScope 模型:
```
模型名称: Qwen/Qwen2.5-72B-Instruct
模型名称: meta-llama/Llama-3.1-70B-Instruct
```

### Azure OpenAI

```
API Key: your-azure-api-key
API Base URL: https://your-resource.openai.azure.com/
模型名称: gpt-4
```

## 配置存储

### 数据库存储

配置保存在 `system_configs` 表中：

| 字段 | 说明 |
|------|------|
| config_key | 配置键（如 OPENAI_API_KEY） |
| config_value | 配置值 |
| description | 配置描述 |
| created_at | 创建时间 |
| updated_at | 更新时间 |

### .env 文件

配置同时会更新到 `backend/.env` 文件中，格式如下：

```env
# Milvus Configuration
MILVUS_HOST=localhost
MILVUS_PORT=19530

# OpenAI/LLM Configuration
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4
```

## 安全注意事项

### 权限控制

- ⚠️ **只有超级管理员**可以访问配置管理页面
- 🔒 普通用户访问会返回 403 Forbidden 错误

### API Key 安全

- 🔐 API Key 在数据库中**明文存储**
- 📋 界面显示时会**自动脱敏**（只显示前4位和后4位）
- 🔄 建议**定期更换** API Key
- 💾 确保数据库访问权限受到严格控制

### 配置文件安全

- 📁 `.env` 文件应该添加到 `.gitignore`
- 🚫 不要将 `.env` 文件提交到版本控制系统
- 🔒 确保服务器文件系统权限正确设置

## 故障排除

### 问题 1: 无法访问配置页面（403 错误）

**原因**: 当前用户不是超级管理员

**解决方案**:
```sql
-- 在数据库中设置用户为超级管理员
UPDATE users SET is_superuser = true WHERE username = 'your_username';
```

### 问题 2: 保存配置后不生效

**原因**: 某些配置需要重启后端才能完全生效

**解决方案**:
1. 停止后端服务（Ctrl+C）
2. 重新启动后端：
   ```bash
   cd backend
   python main.py
   ```

### 问题 3: 数据库表不存在

**错误信息**: `relation "system_configs" does not exist`

**解决方案**:
```bash
create-system-config-table.bat
```

### 问题 4: 配置保存成功但 .env 文件未更新

**原因**: .env 文件权限问题或文件不存在

**解决方案**:
1. 检查 `backend/.env` 文件是否存在
2. 检查文件权限是否可写
3. 如果不存在，从模板创建：
   ```bash
   cd backend
   copy .env.example .env
   ```

## API 接口文档

### 获取 Milvus 配置

```http
GET /api/v1/system-config/milvus
Authorization: Bearer <token>
```

**响应**:
```json
{
  "host": "localhost",
  "port": 19530
}
```

### 更新 Milvus 配置

```http
PUT /api/v1/system-config/milvus
Authorization: Bearer <token>
Content-Type: application/json

{
  "host": "localhost",
  "port": 19530
}
```

### 获取模型配置

```http
GET /api/v1/system-config/model
Authorization: Bearer <token>
```

**响应**:
```json
{
  "api_key": "sk-p****xxx",
  "api_key_full": "sk-proj-xxxxxxxxxxxxx",
  "api_base": "https://api.openai.com/v1",
  "model_name": "gpt-4"
}
```

### 更新模型配置

```http
PUT /api/v1/system-config/model
Authorization: Bearer <token>
Content-Type: application/json

{
  "api_key": "sk-proj-xxxxxxxxxxxxx",
  "api_base": "https://api.openai.com/v1",
  "model_name": "gpt-4"
}
```

## 最佳实践

### 1. 配置管理流程

1. ✅ 首次部署时通过 Web 界面配置
2. ✅ 配置完成后重启后端验证
3. ✅ 定期备份 .env 文件
4. ✅ 生产环境使用环境变量而非 .env 文件

### 2. API Key 管理

1. 🔐 使用专用的 API Key，不要共享个人 Key
2. 🔄 定期轮换 API Key
3. 📊 监控 API 使用量和费用
4. ⚠️ 设置 API 使用限额

### 3. 安全建议

1. 🔒 限制超级管理员账号数量
2. 📝 记录配置变更日志
3. 🔐 使用强密码保护管理员账号
4. 🚫 不要在公共网络上暴露配置接口

## 总结

系统配置管理功能提供了便捷的 Web 界面来管理系统参数，避免了手动编辑配置文件的麻烦。通过合理使用此功能，可以：

- ✅ 快速调整系统配置
- ✅ 减少配置错误
- ✅ 提高运维效率
- ✅ 保证配置安全

记住：**配置修改后建议重启后端**以确保所有配置完全生效！

