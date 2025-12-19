# 自动化测试平台集成说明文档

## 概述

本文档描述了测试用例管理系统与自动化测试平台的集成实现，实现了从测试用例自动匹配场景并在自动化平台创建用例的功能。

## 功能流程

```
测试用例 → 场景匹配 → 创建自动化用例 → 获取支持字段
```

### 详细步骤

1. **场景匹配**：根据测试用例关联的测试点的业务线和模块信息，匹配合适的场景
2. **创建用例**：调用自动化平台的创建用例接口，传入场景ID和模块ID
3. **获取字段**：获取该场景下支持的字段信息

## 后端实现

### 1. 自动化平台服务 (`app/services/automation_service.py`)

#### 服务类：`AutomationPlatformService`

```python
class AutomationPlatformService:
    """自动化测试平台服务类"""
    
    def __init__(self):
        # 从配置读取自动化平台API地址
        self.base_url = settings.AUTOMATION_PLATFORM_API_BASE
```

#### 主要方法

##### `create_case()` - 创建自动化测试用例

**参数：**
- `name`: 测试用例名称
- `module_id`: 模块ID（必填）
- `scene_id`: 场景ID（必填）
- `scenario_type`: 场景类型，默认 "API"
- `description`: 用例描述
- `tags`: 标签，JSON字符串格式
- 其他可选参数...

**请求示例：**
```json
POST /usercase/case/addCase
{
    "name": "测试用例名称",
    "moduleId": "a7f94755-b7c6-42ba-ba12-9026d9760cf5",
    "nodePath": "",
    "tags": "[]",
    "description": "",
    "type": "",
    "project": "",
    "scenarioType": "API",
    "sceneId": "场景编号",
    "sceneIdModule": ""
}
```

**返回示例：**
```json
{
    "success": true,
    "message": null,
    "data": {
        "usercaseId": "8dba1192-7f86-420a-b69e-8e00d06db36a",
        "sceneId": "7fb31238-92df-377a-8ea7-9b437be47710",
        "name": "测试用例",
        "createBy": "admin",
        "createTime": 1765876295618,
        "num": 18880
    }
}
```

##### `get_supported_fields()` - 获取支持的字段

**参数：**
- `scene_id`: 场景ID
- `usercase_id`: 用例ID

**请求示例：**
```
GET /api/automation/bom/variable/{场景id}/{用例usercaseId}
```

##### `create_case_with_fields()` - 创建用例并获取字段

组合方法，先创建用例，然后获取支持的字段。

**返回：**
```json
{
    "case": {...},          // 创建的用例信息
    "fields": {...},        // 支持的字段
    "usercase_id": "...",   // 用例ID
    "scene_id": "..."       // 场景ID
}
```

### 2. API 端点 (`app/api/v1/endpoints/test_cases.py`)

#### POST `/test-cases/{test_case_id}/generate-automation`

生成自动化测试用例的完整流程。

**参数：**
- `test_case_id`: 测试用例ID（路径参数）
- `module_id`: 自动化平台的模块ID（查询参数，必填）

**处理流程：**

1. **验证服务可用性**
   ```python
   if not automation_service:
       raise HTTPException(status_code=503, detail="自动化测试平台服务未配置或不可用")
   ```

2. **查询测试用例**
   ```python
   test_case = db.query(TestCase).join(TestPoint).join(Requirement).filter(
       TestCase.id == test_case_id,
       Requirement.user_id == current_user.id
   ).first()
   ```

3. **场景匹配**
   ```python
   # 优先匹配业务线
   scenarios_query = db.query(Scenario).filter(Scenario.is_active == True)
   if business_line:
       scenarios_query = scenarios_query.filter(Scenario.business_line == business_line)
   
   # 选择第一个匹配的场景
   matched_scenario = scenarios[0]
   ```

4. **创建自动化用例**
   ```python
   result = automation_service.create_case_with_fields(
       name=case_name,
       module_id=module_id,
       scene_id=matched_scenario.scenario_code,  # 使用场景编号作为场景ID
       scenario_type="API",
       description=case_description
   )
   ```

**成功响应：**
```json
{
    "success": true,
    "message": "自动化用例创建成功",
    "data": {
        "test_case": {
            "id": 123,
            "code": "TC001",
            "title": "测试用例标题"
        },
        "matched_scenario": {
            "id": 1,
            "scenario_code": "SC001",
            "name": "场景名称"
        },
        "automation_case": {
            "usercaseId": "...",
            "num": 18880,
            "createBy": "admin",
            "createTime": 1765876295618
        },
        "supported_fields": {...},
        "usercase_id": "...",
        "scene_id": "..."
    }
}
```

**错误响应：**
```json
{
    "detail": "错误信息"
}
```

可能的错误：
- `503`: 自动化测试平台服务未配置或不可用
- `404`: 测试用例不存在 / 未找到可用的场景
- `500`: 创建自动化用例失败

## 前端实现

### 1. API 服务 (`src/services/api.ts`)

```typescript
export const testCasesAPI = {
  // ... 其他方法 ...
  
  // 生成自动化用例
  generateAutomation: (id: number, moduleId: string) => 
    api.post(`/test-cases/${id}/generate-automation`, null, { 
      params: { module_id: moduleId } 
    }),
}
```

### 2. 测试用例页面 (`src/pages/TestCases.tsx`)

#### 触发入口

在测试用例表格的操作列添加"自动化"按钮：

```tsx
<Tooltip title="生成自动化用例">
  <Button
    type="link"
    icon={<RobotOutlined />}
    size="small"
    onClick={() => handleGenerateAutomation(record)}
  >
    自动化
  </Button>
</Tooltip>
```

#### 处理函数：`handleGenerateAutomation`

**功能流程：**

1. **弹出输入框**：要求用户输入模块ID
   ```tsx
   Modal.confirm({
     title: '生成自动化测试用例',
     content: (
       <div>
         <p>请输入自动化平台的模块ID：</p>
         <Input
           id="moduleIdInput"
           placeholder="例如：a7f94755-b7c6-42ba-ba12-9026d9760cf5"
         />
       </div>
     ),
     // ...
   })
   ```

2. **调用API**：
   ```tsx
   const response = await testCasesAPI.generateAutomation(
     testCase.id, 
     moduleId.trim()
   )
   ```

3. **显示结果**：成功时展示详细信息
   ```tsx
   Modal.success({
     title: '自动化用例创建成功',
     content: (
       <Descriptions>
         <Descriptions.Item label="测试用例">...</Descriptions.Item>
         <Descriptions.Item label="匹配场景">...</Descriptions.Item>
         <Descriptions.Item label="自动化用例ID">...</Descriptions.Item>
         <Descriptions.Item label="支持的字段">...</Descriptions.Item>
       </Descriptions>
     )
   })
   ```

## 配置

### 后端配置 (`app/core/config.py`)

添加自动化平台配置：

```python
class Settings(BaseSettings):
    # ... 其他配置 ...
    
    # 自动化测试平台配置
    AUTOMATION_PLATFORM_API_BASE: Optional[str] = None
```

### 环境变量 (`.env`)

```bash
# 自动化测试平台API地址
AUTOMATION_PLATFORM_API_BASE=http://your-automation-platform.com
```

## 使用指南

### 前置条件

1. **配置自动化平台地址**
   - 在后端 `.env` 文件中配置 `AUTOMATION_PLATFORM_API_BASE`
   - 重启后端服务

2. **创建场景**
   - 在"场景管理"页面创建场景
   - 设置场景编号、名称、业务线等信息
   - 确保场景状态为"启用"

3. **获取模块ID**
   - 从自动化测试平台获取目标模块的ID
   - 通常是UUID格式，如：`a7f94755-b7c6-42ba-ba12-9026d9760cf5`

### 操作步骤

1. **进入测试用例页面**
   - 导航到"测试用例"页面
   - 找到要生成自动化用例的测试用例

2. **点击自动化按钮**
   - 在操作列点击"自动化"按钮
   - 弹出输入框

3. **输入模块ID**
   - 在输入框中输入自动化平台的模块ID
   - 点击"生成"按钮

4. **查看结果**
   - 成功：显示匹配的场景、创建的用例ID、支持的字段等信息
   - 失败：显示错误信息

### 场景匹配规则

系统按以下优先级匹配场景：

1. **业务线匹配**：优先匹配与测试点相同业务线的场景
2. **模块匹配**：在业务线匹配的基础上，进一步匹配模块
3. **默认匹配**：如果没有精确匹配，选择第一个启用的场景

**示例：**

测试点信息：
- 业务线：`contract`（契约）
- 模块：`policy_creation`（保单创建）

场景匹配逻辑：
```python
# 1. 优先匹配业务线和模块都符合的场景
matched = Scenario.filter(
    business_line == 'contract',
    module == 'policy_creation',
    is_active == True
)

# 2. 如果没有，匹配业务线
if not matched:
    matched = Scenario.filter(
        business_line == 'contract',
        is_active == True
    )

# 3. 如果还没有，使用任意启用的场景
if not matched:
    matched = Scenario.filter(is_active == True)
```

## 错误处理

### 常见错误及解决方案

| 错误代码 | 错误信息 | 原因 | 解决方案 |
|---------|---------|------|---------|
| 503 | 自动化测试平台服务未配置或不可用 | 未配置 `AUTOMATION_PLATFORM_API_BASE` | 在 `.env` 中配置自动化平台地址 |
| 404 | 测试用例不存在 | 测试用例ID无效或无权限 | 检查测试用例是否存在且属于当前用户 |
| 404 | 未找到可用的场景 | 场景管理中没有启用的场景 | 在场景管理中创建并启用场景 |
| 500 | 创建自动化用例失败 | 自动化平台API调用失败 | 检查网络连接、API地址、参数格式 |

### 调试建议

1. **检查后端日志**
   ```bash
   # 查看详细错误信息
   tail -f backend.log
   ```

2. **验证配置**
   ```python
   # 在 Python 环境中测试
   from app.services.automation_service import automation_service
   print(automation_service.base_url if automation_service else "Not configured")
   ```

3. **测试API连接**
   ```bash
   # 测试自动化平台API是否可访问
   curl -X POST http://your-platform.com/usercase/case/addCase \
     -H "Content-Type: application/json" \
     -d '{"name":"test",...}'
   ```

## API 测试示例

### 使用 curl

```bash
# 1. 生成自动化用例
curl -X POST "http://localhost:8000/api/v1/test-cases/123/generate-automation?module_id=a7f94755-b7c6-42ba-ba12-9026d9760cf5" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

### 使用 Python

```python
import requests

# API配置
BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_access_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 生成自动化用例
test_case_id = 123
module_id = "a7f94755-b7c6-42ba-ba12-9026d9760cf5"

response = requests.post(
    f"{BASE_URL}/test-cases/{test_case_id}/generate-automation",
    params={"module_id": module_id},
    headers=headers
)

result = response.json()
print(result)
```

## 扩展建议

### 1. 场景匹配优化

- **智能匹配**：使用AI/ML算法提高场景匹配准确率
- **手动选择**：允许用户手动选择场景
- **匹配历史**：记录匹配历史，优化匹配策略

### 2. 批量操作

```python
# 批量生成自动化用例
@router.post("/test-cases/batch-generate-automation")
def batch_generate_automation(
    test_case_ids: List[int],
    module_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    results = []
    for test_case_id in test_case_ids:
        try:
            result = generate_automation_case(test_case_id, module_id, db, current_user)
            results.append({"id": test_case_id, "success": True, "data": result})
        except Exception as e:
            results.append({"id": test_case_id, "success": False, "error": str(e)})
    return {"results": results}
```

### 3. 同步状态

- 定期同步自动化平台的用例状态
- 展示执行结果和统计信息
- 支持从自动化平台导入结果

### 4. 配置管理

```python
# 支持多个自动化平台
AUTOMATION_PLATFORMS = {
    "platform_a": {
        "base_url": "http://platform-a.com",
        "api_key": "xxx"
    },
    "platform_b": {
        "base_url": "http://platform-b.com",
        "api_key": "yyy"
    }
}
```

## 总结

本集成实现了测试用例管理系统与自动化测试平台的无缝对接，主要特点：

✅ **自动化流程**：一键生成自动化用例  
✅ **智能匹配**：根据业务线和模块自动匹配场景  
✅ **详细反馈**：展示创建结果和支持的字段  
✅ **错误处理**：完善的错误提示和处理机制  
✅ **可扩展性**：支持后续功能扩展

## 相关文档

- [场景管理模块说明](./SCENARIO_COMPLETE_GUIDE.md)
- [API文档](./backend/SCENARIO_MODULE_README.md)
- [后端配置说明](./backend/app/core/config.py)


