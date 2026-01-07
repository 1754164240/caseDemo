# 自动化平台配置更新说明

## 📋 更新内容

将自动化测试平台的API地址和模块ID统一配置到系统配置中，无需每次手动输入。

## ✨ 主要改进

### 1. 配置集中管理

所有自动化平台相关配置统一在**系统配置**中管理：
- ✅ API地址
- ✅ 默认模块ID

### 2. 自动读取配置

生成自动化用例时：
- 如果系统配置了模块ID，会自动预填充
- 用户可以直接使用系统配置的模块ID，也可以临时修改
- 如果未输入且系统未配置，会给出明确提示

### 3. 更好的用户体验

- 系统配置后，生成用例更加便捷
- 支持一键生成（使用系统配置）
- 也支持临时覆盖（手动输入不同的模块ID）

## 🔧 配置方法

### 步骤 1：进入系统配置

1. 使用管理员账号登录
2. 导航到"系统配置"页面
3. 找到"自动化测试平台配置"部分

### 步骤 2：配置参数

填写以下信息：

```
API地址：http://your-automation-platform.com
模块ID：a7f94755-b7c6-42ba-ba12-9026d9760cf5
```

### 步骤 3：保存配置

点击"保存"按钮，配置立即生效。

## 📝 使用方法

### 方式一：使用系统配置（推荐）

1. 在系统配置中设置好API地址和模块ID
2. 在测试用例列表点击"自动化"按钮
3. 对话框中会自动填充系统配置的模块ID
4. 直接点击"生成"按钮即可

### 方式二：临时覆盖

1. 在测试用例列表点击"自动化"按钮
2. 对话框中会显示系统配置的模块ID
3. 可以修改为其他模块ID
4. 点击"生成"按钮

### 方式三：不使用系统配置

如果系统未配置模块ID：
1. 点击"自动化"按钮
2. 手动输入模块ID
3. 点击"生成"按钮

## 🔄 API 变更

### 后端变更

#### 1. 系统配置 Schema 更新

**文件**：`backend/app/schemas/system_config.py`

```python
class AutomationPlatformConfigUpdate(BaseModel):
    """自动化测试平台配置"""
    api_base: str
    module_id: str  # 新增字段
```

#### 2. 系统配置 API 更新

**GET `/api/v1/system-config/automation-platform`**

响应：
```json
{
  "api_base": "http://your-platform.com",
  "module_id": "a7f94755-b7c6-42ba-ba12-9026d9760cf5"
}
```

**PUT `/api/v1/system-config/automation-platform`**

请求：
```json
{
  "api_base": "http://your-platform.com",
  "module_id": "a7f94755-b7c6-42ba-ba12-9026d9760cf5"
}
```

#### 3. 生成自动化用例 API 更新

**POST `/api/v1/test-cases/{test_case_id}/generate-automation`**

参数变更：
- `module_id` 现在是**可选参数**
- 如果不传，从系统配置读取
- 如果系统配置也没有，返回 400 错误

**请求示例 1**（使用系统配置）：
```bash
curl -X POST "http://localhost:8000/api/v1/test-cases/123/generate-automation" \
  -H "Authorization: Bearer {token}"
```

**请求示例 2**（临时指定）：
```bash
curl -X POST "http://localhost:8000/api/v1/test-cases/123/generate-automation?module_id=custom-id" \
  -H "Authorization: Bearer {token}"
```

**错误响应**（未配置模块ID）：
```json
{
  "detail": "模块ID未提供，且系统配置中未配置默认模块ID，请先在系统配置中配置自动化测试平台的模块ID"
}
```

### 前端变更

#### 1. API Service 更新

**文件**：`frontend/src/services/api.ts`

```typescript
// 系统配置 API
export const systemConfigAPI = {
  // 自动化测试平台配置
  getAutomationPlatformConfig: () => api.get('/system-config/automation-platform'),
  updateAutomationPlatformConfig: (data: { 
    api_base: string; 
    module_id: string  // 新增字段
  }) => api.put('/system-config/automation-platform', data),
}

// 测试用例 API
export const testCasesAPI = {
  // 生成自动化用例（module_id 现在可选）
  generateAutomation: (id: number, moduleId?: string) => 
    api.post(`/test-cases/${id}/generate-automation`, null, { 
      params: moduleId ? { module_id: moduleId } : undefined 
    }),
}
```

#### 2. 测试用例页面更新

**文件**：`frontend/src/pages/TestCases.tsx`

**新增功能**：
1. 加载自动化平台配置
2. 自动填充默认模块ID
3. 智能提示（已配置/未配置）
4. 支持临时覆盖

**关键代码**：
```typescript
// 状态
const [defaultModuleId, setDefaultModuleId] = useState<string>('')

// 加载配置
const loadAutomationConfig = async () => {
  try {
    const response = await systemConfigAPI.getAutomationPlatformConfig()
    if (response.data?.module_id) {
      setDefaultModuleId(response.data.module_id)
    }
  } catch (error) {
    console.error('加载自动化平台配置失败:', error)
  }
}

// 生成自动化用例
const handleGenerateAutomation = async (testCase: any) => {
  Modal.confirm({
    content: (
      <div>
        <Input
          id="moduleIdInput"
          placeholder={defaultModuleId || '例如：xxx'}
          defaultValue={defaultModuleId}  // 预填充系统配置
        />
        {defaultModuleId && (
          <div style={{ color: '#52c41a' }}>
            ✓ 系统已配置默认模块ID，可直接生成
          </div>
        )}
      </div>
    ),
    onOk: async () => {
      const moduleId = inputValue?.trim() || defaultModuleId
      // ... 调用 API
    }
  })
}
```

## 💡 使用场景

### 场景 1：固定模块开发

如果团队只使用一个固定的模块：
1. 在系统配置中设置好模块ID
2. 所有用户生成自动化用例时直接使用系统配置
3. 无需每次输入

### 场景 2：多模块开发

如果需要针对不同模块生成用例：
1. 在系统配置中设置常用模块ID（默认值）
2. 生成用例时，根据需要临时修改模块ID
3. 灵活方便

### 场景 3：新用户引导

对于新用户：
1. 管理员提前配置好系统参数
2. 新用户无需了解配置细节
3. 开箱即用

## 🔍 配置查看

### 方法一：前端界面查看

1. 登录系统（管理员账号）
2. 进入"系统配置"页面
3. 查看"自动化测试平台配置"部分

### 方法二：API 查看

```bash
# 获取配置
curl -X GET "http://localhost:8000/api/v1/system-config/automation-platform" \
  -H "Authorization: Bearer {admin_token}"
```

响应：
```json
{
  "api_base": "http://your-platform.com",
  "module_id": "a7f94755-b7c6-42ba-ba12-9026d9760cf5"
}
```

### 方法三：数据库查看

```sql
-- 查看配置
SELECT * FROM system_configs 
WHERE config_key IN ('AUTOMATION_PLATFORM_API_BASE', 'AUTOMATION_PLATFORM_MODULE_ID');
```

## 📊 配置优先级

生成自动化用例时的模块ID优先级：

```
1. 用户手动输入（优先级最高）
   ↓
2. 系统配置的默认值
   ↓
3. 无配置（报错提示）
```

**示例：**

| 系统配置 | 用户输入 | 实际使用 | 说明 |
|---------|---------|---------|------|
| `moduleA` | `moduleB` | `moduleB` | 使用用户输入 |
| `moduleA` | 空 | `moduleA` | 使用系统配置 |
| 空 | `moduleB` | `moduleB` | 使用用户输入 |
| 空 | 空 | 错误 | 必须提供模块ID |

## 🎯 最佳实践

### 1. 推荐配置策略

**小型团队**：
- 配置统一的模块ID
- 所有人使用系统配置
- 简化操作流程

**大型团队**：
- 配置最常用的模块ID作为默认值
- 特殊情况时临时修改
- 兼顾效率和灵活性

### 2. 配置管理建议

- 定期检查配置是否过期
- 模块ID变更时及时更新系统配置
- 为不同环境（开发/测试/生产）配置不同的模块ID

### 3. 权限控制

- 只有管理员可以修改系统配置
- 普通用户只能使用配置，不能修改
- 确保配置的稳定性和安全性

## 🐛 故障排除

### 问题 1：配置不生效

**症状**：修改了系统配置，但前端仍显示旧值

**解决**：
1. 刷新前端页面（F5）
2. 重新打开"生成自动化用例"对话框
3. 清除浏览器缓存

### 问题 2：无法保存配置

**症状**：点击保存后提示失败

**原因**：
- 没有管理员权限
- 配置格式不正确
- 网络连接问题

**解决**：
1. 确认使用管理员账号登录
2. 检查配置格式（API地址、模块ID格式）
3. 查看浏览器控制台错误信息

### 问题 3：生成失败提示"未配置模块ID"

**症状**：点击生成按钮后提示需要配置模块ID

**解决**：
1. 检查系统配置中是否设置了模块ID
2. 或在对话框中手动输入模块ID
3. 保存配置后重试

## 📈 后续优化建议

### v1.3 计划

- [ ] 支持多个模块ID配置
- [ ] 支持按业务线配置不同的模块ID
- [ ] 支持用户级别的个性化配置
- [ ] 配置模板功能

### v1.4 计划

- [ ] 配置导入/导出功能
- [ ] 配置变更历史记录
- [ ] 配置审计日志
- [ ] 批量配置管理

## 📞 技术支持

遇到问题请参考：
1. [快速开始指南](./AUTOMATION_QUICK_START.md)
2. [完整集成文档](./AUTOMATION_PLATFORM_INTEGRATION.md)
3. [环境配置说明](../backend/ENVIRONMENT_SETUP.md)

---

**更新日期**：2024-12-16  
**版本**：v1.2.1  
**变更类型**：功能增强





