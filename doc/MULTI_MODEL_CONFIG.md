# 模型配置支持多模型功能

## 功能概述

将模型配置从**单模型**升级为**多模型**支持，允许在一个配置中设置多个模型名称，系统将按顺序尝试调用。

### 使用场景

1. **模型降级**: 主模型不可用时自动切换到备用模型
   - 示例：`["gpt-4", "gpt-3.5-turbo"]` - GPT-4不可用时使用GPT-3.5

2. **成本优化**: 优先使用便宜的模型，失败时使用高级模型
   - 示例：`["glm-4-air", "glm-4", "gpt-4"]`

3. **A/B测试**: 在不同模型间切换测试效果
   - 示例：`["gpt-4-turbo-preview", "claude-3-opus"]`

4. **负载均衡**: 在多个相同模型实例间分配请求
   - 示例：`["model-v1-instance1", "model-v1-instance2"]`

## 核心变更

### 1. 数据结构变更

**之前**：
```json
{
  "model_name": "gpt-4"
}
```

**之后**：
```json
{
  "model_name": ["gpt-4", "gpt-3.5-turbo", "glm-4"]
}
```

### 2. 数据库Schema变更

```sql
-- 字段类型：VARCHAR(200) → TEXT
ALTER TABLE model_configs ALTER COLUMN model_name TYPE TEXT;

-- 字段注释更新
COMMENT ON COLUMN model_configs.model_name IS
  '模型名称列表(JSON数组格式,如["gpt-4","gpt-3.5-turbo"])';
```

### 3. API变更

#### 创建/更新模型配置

**请求示例**：
```json
{
  "name": "openai-multi",
  "display_name": "OpenAI 多模型配置",
  "api_key": "sk-xxxxx",
  "api_base": "https://api.openai.com/v1",
  "model_name": ["gpt-4", "gpt-3.5-turbo"],  // 数组格式
  "temperature": "0.7",
  "provider": "openai"
}
```

**向后兼容**：
```json
{
  "model_name": "gpt-4"  // 单个字符串也支持，会自动转换为 ["gpt-4"]
}
```

#### 查询模型配置

**响应示例**：
```json
{
  "id": 1,
  "name": "openai-multi",
  "model_name": ["gpt-4", "gpt-3.5-turbo"],  // 始终返回数组
  ...
}
```

### 4. 前端界面变更

#### 模型配置表格

**显示效果**：
```
模型信息列：
┌──────────────────────┐
│ [gpt-4] [gpt-3.5-turbo]│
│ [glm-4]              │
│ openai               │
│ https://api.openai...│
└──────────────────────┘
```

#### 编辑表单

- **多选下拉框**：支持选择多个预设模型
- **自定义输入**：支持手动输入模型名称
- **拖拽排序**：后续可增加，调整模型调用顺序

## 修改文件清单

### 后端修改

| 文件 | 修改内容 |
|------|---------|
| `backend/app/models/model_config.py` | 字段注释更新 |
| `backend/app/schemas/model_config.py` | Schema支持List[str] |
| `backend/app/api/v1/endpoints/model_config.py` | 添加序列化/反序列化函数 |

### 前端修改

| 文件 | 修改内容 |
|------|---------|
| `frontend/src/pages/ModelConfigs.tsx` | 多选下拉框 + 表格展示 |

### 迁移脚本

| 文件 | 用途 |
|------|------|
| `backend/scripts/migrate_model_name_to_array.sql` | SQL迁移脚本 |
| `backend/scripts/migrate_model_name_to_array.py` | Python迁移脚本 |

## 实施步骤

### 1. 数据库迁移

**方式A：使用Python脚本（推荐）**

```bash
cd backend
python scripts/migrate_model_name_to_array.py
```

**方式B：手动执行SQL**

```sql
-- 在PostgreSQL中执行
\i scripts/migrate_model_name_to_array.sql
```

### 2. 重启后端服务

```bash
cd backend
python -m scripts.main
```

### 3. 刷新前端页面

访问模型配置页面，验证功能：
- 现有配置显示为数组格式
- 可以创建多模型配置
- 表格正确展示多个模型

### 4. 测试验证

#### 测试用例1：创建多模型配置

```json
{
  "name": "test-multi",
  "display_name": "测试多模型",
  "api_key": "sk-test",
  "api_base": "https://api.test.com",
  "model_name": ["gpt-4", "gpt-3.5-turbo", "glm-4"]
}
```

#### 测试用例2：更新为单模型

```json
{
  "model_name": ["gpt-4"]
}
```

#### 测试用例3：向后兼容（单字符串）

```json
{
  "model_name": "gpt-4"  // 应自动转换为 ["gpt-4"]
}
```

## 向后兼容性

### 1. 数据兼容

- ✅ 现有单模型配置自动转换为数组格式
- ✅ API仍接受单个字符串，自动包装为数组
- ✅ 旧版客户端也能正常工作

### 2. AI服务调用

**调用逻辑（建议）**：
```python
def get_model_for_request(config):
    """从配置中获取模型名称"""
    models = config.model_name  # 现在是数组

    # 按顺序尝试
    for model in models:
        try:
            # 使用该模型调用AI
            return call_ai_with_model(model)
        except Exception as e:
            print(f"模型 {model} 调用失败: {e}")
            continue

    raise Exception("所有模型都不可用")
```

**注意**: 当前AI服务调用逻辑可能需要更新以支持多模型降级，建议在`ai_service.py`中实现。

## 常见问题

### Q1: 模型调用顺序是什么？

A: 按数组顺序调用。数组第一个元素是主模型，后续为备用模型。

### Q2: 所有模型都需要相同的API Key吗？

A: 是的，当前一个配置共用一个API Key。如需不同Key，请创建多个配置。

### Q3: 如何设置模型调用超时？

A: 在AI服务配置中设置，当前为180秒。超时后自动尝试下一个模型。

### Q4: 最多支持多少个模型？

A: 理论上无限制，但建议不超过5个，避免降级链过长。

### Q5: 旧数据会丢失吗？

A: 不会。迁移脚本会将所有单模型名称转换为包含一个元素的数组。

## 后续优化建议

### 1. 模型优先级和权重

```json
{
  "model_name": [
    {"name": "gpt-4", "weight": 0.7},
    {"name": "gpt-3.5-turbo", "weight": 0.3"}
  ]
}
```

### 2. 按场景选择模型

```python
def get_model_by_task(config, task_type):
    if task_type == "code_generation":
        return config.model_name[0]  # 最强模型
    elif task_type == "chat":
        return config.model_name[-1]  # 最便宜模型
```

### 3. 实时监控和切换

- 记录每个模型的成功率和延迟
- 自动禁用表现差的模型
- 在前端显示模型健康度

### 4. 模型分组管理

```json
{
  "primary": ["gpt-4", "claude-3-opus"],
  "fallback": ["gpt-3.5-turbo", "glm-4"],
  "emergency": ["qwen-turbo"]
}
```

## 相关文档

- [模型配置API文档](./MODEL_CONFIG_API.md)
- [AI服务调用逻辑](./AI_SERVICE.md)
- [数据库Schema设计](./DATABASE_SCHEMA.md)

---

**修改时间**: 2026-02-03
**状态**: 已实施
**影响范围**: 模型配置模块、AI服务调用
