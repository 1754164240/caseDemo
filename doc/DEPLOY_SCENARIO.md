# 场景管理模块 - 快速部署指南

## 🎯 部署步骤

### 步骤 1: 重启后端服务 ⚠️ 必须执行

**Windows PowerShell:**
```powershell
cd D:\caseDemo1\backend

# 停止现有服务（如果正在运行）
# 按 Ctrl+C 停止

# 重新启动服务
python main.py
```

**预期输出：**
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 步骤 2: 验证数据库表创建

服务启动时会自动创建 `scenarios` 表。

**验证方法：**
```sql
-- 连接到 PostgreSQL 数据库
psql -U postgres -d test_case_db

-- 查看表结构
\d scenarios

-- 查询表（应该为空）
SELECT * FROM scenarios;
```

**预期表结构：**
```
Column        | Type                     | Nullable
--------------+--------------------------+----------
id            | integer                  | not null
scenario_code | character varying(50)    | not null
name          | character varying(200)   | not null
description   | text                     |
business_line | character varying(50)    |
channel       | character varying(100)   |
module        | character varying(100)   |
is_active     | boolean                  |
created_at    | timestamp with time zone |
updated_at    | timestamp with time zone |
```

### 步骤 3: 验证 API 可用

**方法 A: 浏览器访问 Swagger UI**

打开浏览器访问：
```
http://localhost:8000/docs
```

在页面中查找 **"场景管理"** 标签，应该看到以下接口：
- `GET /api/v1/scenarios/` - 获取场景列表
- `POST /api/v1/scenarios/` - 创建场景
- `GET /api/v1/scenarios/{scenario_id}` - 获取单个场景
- `PUT /api/v1/scenarios/{scenario_id}` - 更新场景
- `DELETE /api/v1/scenarios/{scenario_id}` - 删除场景
- `GET /api/v1/scenarios/code/{scenario_code}` - 通过编号获取场景
- `POST /api/v1/scenarios/{scenario_id}/toggle-status` - 切换状态

**方法 B: 使用 curl 测试**

```bash
# 测试获取场景列表（需要登录）
curl -X GET "http://localhost:8000/api/v1/scenarios/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 步骤 4: 获取 JWT Token（首次使用）

如果还没有 Token，需要先登录：

```bash
# 登录获取 Token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

**响应示例：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

复制 `access_token` 的值，在后续请求中使用。

### 步骤 5: 创建第一个场景

**使用 Swagger UI（推荐）：**
1. 访问 http://localhost:8000/docs
2. 点击右上角 "Authorize" 按钮
3. 输入 Token：`Bearer YOUR_TOKEN`
4. 点击 "Authorize" 确认
5. 找到 `POST /api/v1/scenarios/` 接口
6. 点击 "Try it out"
7. 输入场景数据：

```json
{
  "scenario_code": "SC-001",
  "name": "测试场景",
  "description": "这是第一个测试场景",
  "business_line": "contract",
  "channel": "移动端",
  "module": "测试模块",
  "is_active": true
}
```

8. 点击 "Execute"
9. 查看响应结果

**使用 curl：**
```bash
curl -X POST "http://localhost:8000/api/v1/scenarios/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_code": "SC-001",
    "name": "测试场景",
    "description": "这是第一个测试场景",
    "business_line": "contract",
    "channel": "移动端",
    "module": "测试模块",
    "is_active": true
  }'
```

### 步骤 6: 验证场景已创建

```bash
# 获取场景列表
curl -X GET "http://localhost:8000/api/v1/scenarios/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**预期响应：**
```json
[
  {
    "id": 1,
    "scenario_code": "SC-001",
    "name": "测试场景",
    "description": "这是第一个测试场景",
    "business_line": "contract",
    "channel": "移动端",
    "module": "测试模块",
    "is_active": true,
    "created_at": "2024-01-01T10:00:00+08:00",
    "updated_at": "2024-01-01T10:00:00+08:00"
  }
]
```

## ✅ 部署验证清单

完成以下检查以确保部署成功：

- [ ] 后端服务已重启
- [ ] 服务启动无错误
- [ ] 数据库表 `scenarios` 已创建
- [ ] API 文档中可以看到"场景管理"标签
- [ ] 可以使用 Token 访问场景接口
- [ ] 成功创建了第一个测试场景
- [ ] 可以查询到创建的场景

## 🔍 故障排查

### 问题 1: 找不到"场景管理"标签

**原因**: 服务没有重启或路由注册失败

**解决方案**:
1. 确保服务已重启
2. 检查终端输出是否有错误信息
3. 访问 http://localhost:8000/docs 刷新页面

### 问题 2: 401 Unauthorized

**原因**: Token 无效或未提供

**解决方案**:
1. 确保已登录获取有效 Token
2. 检查 Token 是否正确复制
3. 确保 Token 格式为 `Bearer YOUR_TOKEN`

### 问题 3: 404 Not Found

**原因**: URL 路径错误

**解决方案**:
1. 确保使用正确的路径：`/api/v1/scenarios/`
2. 检查服务是否在 8000 端口运行

### 问题 4: 数据库表未创建

**原因**: 模型未正确注册

**解决方案**:
1. 检查 `app/db/base.py` 中是否导入了 Scenario 模型
2. 重启服务
3. 查看启动日志是否有错误

### 问题 5: 场景编号已存在

**原因**: 尝试创建重复的场景编号

**解决方案**:
1. 使用不同的场景编号
2. 或删除现有场景后重新创建

## 📋 批量导入示例数据（可选）

如果需要快速导入测试数据，可以使用提供的测试脚本：

```bash
# 1. 编辑 test_scenario_api.py
# 2. 替换其中的 TOKEN 变量
# 3. 运行脚本
python test_scenario_api.py
```

该脚本会自动创建 3 个测试场景（契约、保全、理赔各一个）。

## 🎉 部署完成

恭喜！场景管理模块已成功部署。

### 下一步：

1. **查阅详细文档**: `SCENARIO_MODULE_README.md`
2. **运行测试**: `test_scenario_api.py`
3. **开始使用**: 在 Swagger UI 中测试各个接口

### 常用操作：

- **查看所有场景**: `GET /api/v1/scenarios/`
- **创建场景**: `POST /api/v1/scenarios/`
- **更新场景**: `PUT /api/v1/scenarios/{id}`
- **删除场景**: `DELETE /api/v1/scenarios/{id}`
- **搜索场景**: `GET /api/v1/scenarios/?search=关键字`
- **筛选场景**: `GET /api/v1/scenarios/?business_line=contract`

## 📞 需要帮助？

- 查看 API 文档: http://localhost:8000/docs
- 查看详细说明: `SCENARIO_MODULE_README.md`
- 查看开发总结: `SCENARIO_MODULE_SUMMARY.md`

