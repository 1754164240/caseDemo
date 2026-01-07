# 测试用例场景匹配功能说明

## 🎯 功能概述

为测试用例自动匹配对应的场景，返回场景编号，用于生成自动化测试用例。

## ✅ 已实现的功能

### 1. 后端 API

**接口**: `POST /api/v1/test-cases/{test_case_id}/match-scenario`

**功能**:
- 根据测试用例的业务线、标题、描述等信息智能匹配场景
- 返回匹配的场景编号和详细信息

**匹配逻辑**:
1. **业务线匹配**: 优先匹配相同业务线的场景
2. **关键词匹配**: 基于测试用例和场景的标题、描述进行关键词重叠度计算
3. **兜底策略**: 如果没有完全匹配，返回第一个启用的场景

**响应示例**:
```json
{
  "matched": true,
  "scenario_code": "SC-001",
  "scenario_name": "在线投保",
  "scenario": {
    "id": 1,
    "scenario_code": "SC-001",
    "name": "在线投保",
    "description": "用户通过移动端APP进行在线投保",
    "business_line": "contract",
    "channel": "移动端",
    "module": "投保模块"
  },
  "test_case": {
    "id": 1,
    "code": "TP-001-1",
    "title": "测试在线投保流程",
    "business_line": "contract"
  },
  "message": "成功匹配到场景: SC-001"
}
```

### 2. 前端功能

**位置**: 测试用例管理 → 操作列 → "自动化"按钮

**功能**:
1. 点击"自动化"按钮
2. 自动调用后端API匹配场景
3. 显示匹配结果（场景编号和详细信息）
4. 弹出详情对话框展示完整的匹配信息

**UI展示**:
- ✅ 成功消息提示（包含场景编号和名称）
- ✅ 详细信息对话框（Descriptions组件）
- ✅ 显示测试用例和场景的完整信息

## 📊 使用场景

### 场景 1: 契约业务线测试用例

**测试用例信息**:
- 标题: "在线投保功能测试"
- 业务线: contract

**匹配结果**:
- 场景编号: SC-CONTRACT-001
- 场景名称: "在线投保"

### 场景 2: 保全业务线测试用例

**测试用例信息**:
- 标题: "保单变更流程测试"
- 业务线: preservation

**匹配结果**:
- 场景编号: SC-PRESERVATION-001
- 场景名称: "保单变更"

### 场景 3: 理赔业务线测试用例

**测试用例信息**:
- 标题: "理赔申请测试"
- 业务线: claim

**匹配结果**:
- 场景编号: SC-CLAIM-001
- 场景名称: "理赔申请"

## 🔧 使用方法

### 步骤 1: 准备场景数据

在"场景管理"页面创建场景：
```
场景名称: 在线投保
业务线: contract (契约)
渠道: 移动端
模块: 投保模块
状态: 启用
```

### 步骤 2: 测试用例匹配

1. 进入"用例管理"页面
2. 找到要生成自动化的测试用例
3. 点击操作列的"自动化"按钮（机器人图标 🤖）
4. 系统自动匹配场景并显示结果

### 步骤 3: 查看匹配结果

**成功消息**:
```
匹配成功！
场景编号：SC-001
场景名称：在线投保
```

**详情对话框显示**:
- 测试用例编号
- 测试用例标题
- 场景编号（蓝色标签）
- 场景名称
- 场景描述
- 业务线
- 渠道
- 模块

## 🎨 界面效果

### 1. 按钮样式
```
[查看] [编辑] [审批/重置] [自动化 🤖] [删除]
```

### 2. 成功提示
- 绿色成功提示消息
- 显示5秒钟
- 包含场景编号和名称

### 3. 详情对话框
- 宽度：600px
- 标题："场景匹配成功"
- 使用Descriptions组件展示详细信息
- 带边框的表格布局

## 🔍 匹配算法说明

### 1. 业务线优先匹配
```python
if business_line:
    scenarios = scenarios.filter(business_line == test_case.business_line)
```

### 2. 关键词重叠度计算
```python
test_case_keywords = set(test_case.title.split() + test_case.description.split())
scenario_keywords = set(scenario.name.split() + scenario.description.split())
overlap_score = len(test_case_keywords & scenario_keywords)
```

### 3. 选择最佳匹配
- 选择关键词重叠度最高的场景
- 如果没有重叠，返回第一个场景
- 优先返回启用状态的场景

## ⚠️ 注意事项

### 1. 场景准备
- 确保已创建相应的场景
- 场景状态必须为"启用"
- 建议场景的业务线与测试用例一致

### 2. 匹配准确性
- 匹配基于关键词，建议场景命名清晰
- 测试用例标题和描述越详细，匹配越准确
- 可以手动调整匹配结果（后续功能）

### 3. 无匹配场景
如果没有匹配的场景，系统会提示：
```
未找到匹配的场景，请先创建场景
```

## 🚀 后续扩展

### 1. AI智能匹配
使用大语言模型进行语义匹配：
```python
# 使用 AI 进行语义相似度计算
similarity = ai_service.calculate_similarity(
    test_case.description,
    scenario.description
)
```

### 2. 手动选择场景
允许用户在匹配结果中手动选择场景：
```typescript
<Select>
  {matchedScenarios.map(scenario => (
    <Option value={scenario.id}>{scenario.name}</Option>
  ))}
</Select>
```

### 3. 匹配历史记录
记录测试用例和场景的匹配历史：
```python
class TestCaseScenarioMapping(Base):
    test_case_id = Column(Integer, ForeignKey("test_cases.id"))
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    matched_at = Column(DateTime)
```

### 4. 批量匹配
支持批量为多个测试用例匹配场景：
```typescript
const handleBatchMatch = async (testCaseIds: number[]) => {
  for (const id of testCaseIds) {
    await testCasesAPI.matchScenario(id)
  }
}
```

## 📝 API文档

### 请求
```http
POST /api/v1/test-cases/{test_case_id}/match-scenario
Authorization: Bearer {token}
```

### 响应（成功）
```json
{
  "matched": true,
  "scenario_code": "SC-001",
  "scenario_name": "在线投保",
  "scenario": { ... },
  "test_case": { ... },
  "message": "成功匹配到场景: SC-001"
}
```

### 响应（失败）
```json
{
  "matched": false,
  "message": "未找到匹配的场景，请先创建场景",
  "test_case": { ... }
}
```

## ✅ 验证步骤

### 1. 创建场景
```bash
# 访问场景管理页面
http://localhost:3000/scenarios

# 创建测试场景
场景名称: 测试场景
业务线: contract
```

### 2. 测试匹配
```bash
# 访问用例管理页面
http://localhost:3000/test-cases

# 点击"自动化"按钮
# 查看匹配结果
```

### 3. 验证响应
- 检查是否显示场景编号
- 检查详情对话框是否正确显示
- 验证业务线匹配逻辑

---

**完成状态**: ✅ 已完成
**版本**: v1.0
**最后更新**: 2024





