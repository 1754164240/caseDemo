# 场景管理模块使用说明

## 📋 模块概述

场景管理模块提供了完整的场景信息增删改查功能，支持多条件筛选和搜索。

## 🗂️ 数据结构

### 场景字段

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Integer | 自动 | 场景ID（主键） |
| scenario_code | String(50) | 是 | 场景编号，如 SC-001（唯一） |
| name | String(200) | 是 | 场景名称 |
| description | Text | 否 | 场景描述 |
| business_line | String(50) | 否 | 业务线：contract(契约)/preservation(保全)/claim(理赔) |
| channel | String(100) | 否 | 渠道：线上/线下/移动端等 |
| module | String(100) | 否 | 所属模块 |
| is_active | Boolean | 否 | 是否启用（默认 true） |
| created_at | DateTime | 自动 | 创建时间 |
| updated_at | DateTime | 自动 | 更新时间 |

## 🚀 API 接口

### 基础路径
```
/api/v1/scenarios
```

### 1. 获取场景列表
**GET** `/api/v1/scenarios/`

**查询参数：**
- `skip`: 跳过的记录数（默认 0）
- `limit`: 返回的最大记录数（默认 100，最大 500）
- `search`: 搜索关键字（支持场景名称、描述、编号）
- `business_line`: 业务线筛选
- `channel`: 渠道筛选
- `module`: 模块筛选
- `is_active`: 是否启用筛选（true/false）

**示例：**
```bash
# 获取所有场景
curl -X GET "http://localhost:8000/api/v1/scenarios/" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 搜索场景
curl -X GET "http://localhost:8000/api/v1/scenarios/?search=投保&business_line=contract" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 分页查询
curl -X GET "http://localhost:8000/api/v1/scenarios/?skip=0&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例：**
```json
[
  {
    "id": 1,
    "scenario_code": "SC-001",
    "name": "在线投保",
    "description": "用户通过移动端APP进行在线投保流程",
    "business_line": "contract",
    "channel": "移动端",
    "module": "投保模块",
    "is_active": true,
    "created_at": "2024-01-01T10:00:00",
    "updated_at": "2024-01-01T10:00:00"
  }
]
```

### 2. 获取单个场景
**GET** `/api/v1/scenarios/{scenario_id}`

**示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/scenarios/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. 通过编号获取场景
**GET** `/api/v1/scenarios/code/{scenario_code}`

**示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/scenarios/code/SC-001" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. 创建场景
**POST** `/api/v1/scenarios/`

**请求体：**
```json
{
  "scenario_code": "SC-001",
  "name": "在线投保",
  "description": "用户通过移动端APP进行在线投保流程",
  "business_line": "contract",
  "channel": "移动端",
  "module": "投保模块",
  "is_active": true
}
```

**示例：**
```bash
curl -X POST "http://localhost:8000/api/v1/scenarios/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_code": "SC-001",
    "name": "在线投保",
    "description": "用户通过移动端APP进行在线投保流程",
    "business_line": "contract",
    "channel": "移动端",
    "module": "投保模块",
    "is_active": true
  }'
```

### 5. 更新场景
**PUT** `/api/v1/scenarios/{scenario_id}`

**请求体：**（所有字段都是可选的）
```json
{
  "name": "在线投保流程",
  "description": "更新后的描述",
  "is_active": false
}
```

**示例：**
```bash
curl -X PUT "http://localhost:8000/api/v1/scenarios/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "在线投保流程",
    "description": "更新后的描述"
  }'
```

### 6. 删除场景
**DELETE** `/api/v1/scenarios/{scenario_id}`

**示例：**
```bash
curl -X DELETE "http://localhost:8000/api/v1/scenarios/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例：**
```json
{
  "message": "场景 在线投保 (SC-001) 已成功删除"
}
```

### 7. 切换场景状态
**POST** `/api/v1/scenarios/{scenario_id}/toggle-status`

快速切换场景的启用/停用状态。

**示例：**
```bash
curl -X POST "http://localhost:8000/api/v1/scenarios/1/toggle-status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📦 使用示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 创建场景
new_scenario = {
    "scenario_code": "SC-002",
    "name": "保单变更",
    "description": "客户通过线上渠道申请保单信息变更",
    "business_line": "preservation",
    "channel": "线上",
    "module": "保全模块",
    "is_active": True
}

response = requests.post(
    f"{BASE_URL}/scenarios/",
    headers=headers,
    json=new_scenario
)
print(response.json())

# 查询场景列表
response = requests.get(
    f"{BASE_URL}/scenarios/",
    headers=headers,
    params={"business_line": "preservation", "is_active": True}
)
scenarios = response.json()
print(f"找到 {len(scenarios)} 个场景")

# 更新场景
update_data = {
    "description": "客户通过线上渠道申请保单信息变更（含受益人变更）"
}
response = requests.put(
    f"{BASE_URL}/scenarios/1",
    headers=headers,
    json=update_data
)
print(response.json())
```

### JavaScript/TypeScript 示例

```typescript
const BASE_URL = 'http://localhost:8000/api/v1';
const TOKEN = 'your_jwt_token';

const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json'
};

// 创建场景
async function createScenario() {
  const response = await fetch(`${BASE_URL}/scenarios/`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({
      scenario_code: 'SC-003',
      name: '理赔申请',
      description: '客户提交理赔申请',
      business_line: 'claim',
      channel: '移动端',
      module: '理赔模块',
      is_active: true
    })
  });
  
  const data = await response.json();
  console.log('创建成功:', data);
}

// 获取场景列表
async function listScenarios() {
  const params = new URLSearchParams({
    business_line: 'claim',
    is_active: 'true',
    skip: '0',
    limit: '20'
  });
  
  const response = await fetch(`${BASE_URL}/scenarios/?${params}`, {
    headers: headers
  });
  
  const scenarios = await response.json();
  console.log(`找到 ${scenarios.length} 个场景`);
}
```

## 🔍 业务场景示例

### 契约业务线场景
```json
{
  "scenario_code": "SC-CONTRACT-001",
  "name": "在线投保",
  "business_line": "contract",
  "channel": "移动端",
  "module": "投保模块"
}
```

### 保全业务线场景
```json
{
  "scenario_code": "SC-PRESERVATION-001",
  "name": "保单变更",
  "business_line": "preservation",
  "channel": "线上",
  "module": "保全模块"
}
```

### 理赔业务线场景
```json
{
  "scenario_code": "SC-CLAIM-001",
  "name": "理赔申请",
  "business_line": "claim",
  "channel": "移动端",
  "module": "理赔模块"
}
```

## 🗄️ 数据库迁移

重启应用后，数据库表会自动创建。场景表名为 `scenarios`。

如果需要手动检查表结构：

```sql
-- 查看表结构
\d scenarios

-- 查询所有场景
SELECT * FROM scenarios ORDER BY created_at DESC;

-- 按业务线统计
SELECT business_line, COUNT(*) as count 
FROM scenarios 
GROUP BY business_line;
```

## 📊 API 文档

启动服务后，访问以下地址查看完整的 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

在文档中可以看到 **场景管理** 标签，包含所有场景相关的 API。

## ✅ 验证步骤

1. **重启后端服务**
```bash
cd D:\caseDemo1\backend
python main.py
```

2. **访问 API 文档**
```
http://localhost:8000/docs
```

3. **查找"场景管理"标签**
   - 应该能看到所有场景相关的 API 接口

4. **测试创建场景**
   - 使用 Swagger UI 或 curl 创建一个测试场景

## 🎯 功能特性

✅ 完整的 CRUD 操作（增删改查）  
✅ 支持场景编号唯一性校验  
✅ 支持多条件筛选（业务线、渠道、模块、状态）  
✅ 支持关键字搜索（场景名称、描述、编号）  
✅ 支持分页查询  
✅ 支持快速切换启用/停用状态  
✅ 支持通过编号查询场景  
✅ 自动记录创建时间和更新时间  
✅ 需要用户认证（JWT Token）

## 🔐 权限说明

所有场景管理接口都需要用户登录认证。请在请求头中包含有效的 JWT Token：

```
Authorization: Bearer YOUR_JWT_TOKEN
```

## 📞 问题反馈

如有问题或建议，请联系开发团队。

