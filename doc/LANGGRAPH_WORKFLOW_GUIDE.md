# LangGraph 自动化用例工作流 - 使用指南

## 快速开始

### 1. 后端启动

```bash
cd backend
python -m scripts.main
```

### 2. 测试工作流

```bash
cd backend
python -m scripts.test_langgraph_workflow
```

### 3. 前端访问

访问 `http://localhost:5173/automation/workflow/create`

## 工作流说明

### 完整流程图

```
START
  ↓
[节点1] 获取场景用例列表
  ↓
[节点2] AI 选择最佳模板
  ↓
[节点3] 获取详情 + 字段元数据（枚举值、联动规则）
  ↓
[节点4] AI 生成测试数据（带约束）
  ↓
[节点5] 数据校验（枚举值、联动规则、必填字段）
  ↓
┌─────────┴──────────┐
↓                    ↓
有问题需人工审核    无问题自动通过
↓                    ↓
[节点6] 人工审核 ⏸️   [节点8] 创建用例
↓                    ↓
(等待人工输入)       END
↓
[节点7] 应用修改
↓
┌────┴────┐
↓         ↓
通过/修改  拒绝
↓         ↓
创建用例  [节点9] 重新生成
↓         ↓
END    (回到节点4，最多3次)
```

### 状态说明

| 状态 | 说明 | 下一步 |
|------|------|--------|
| `initialized` | 已初始化 | 自动执行 |
| `processing` | 处理中 | 自动执行 |
| `validating` | 校验中 | 自动执行 |
| `reviewing` | 等待人工审核 | **需要人工操作** |
| `approved` | 审核通过 | 自动执行 |
| `rejected` | 审核拒绝 | 自动重新生成 |
| `completed` | 已完成 | 流程结束 |
| `failed` | 失败 | 流程结束 |

## API 使用示例

### 1. 启动工作流

```bash
POST /api/v1/automation/workflow/start
Content-Type: application/json

{
  "name": "理赔测试用例_001",
  "module_id": "MOD_123",
  "scene_id": "SCENE_456",
  "test_case_info": {
    "title": "被保人出险理赔测试",
    "test_steps": "1. 提交申请\n2. 审核\n3. 结案",
    "expected_result": "成功结案"
  }
}
```

**响应**:
```json
{
  "thread_id": "workflow_1_a3f2c9d1",
  "status": "reviewing",
  "current_step": "awaiting_human_review",
  "need_human_review": true,
  "state": {
    "generated_body": [...],
    "validation_result": {...}
  }
}
```

### 2. 提交人工审核

```bash
POST /api/v1/automation/workflow/workflow_1_a3f2c9d1/review
Content-Type: application/json

{
  "review_status": "approved",  // 或 "modified" 或 "rejected"
  "corrected_body": [...],       // 可选：修正后的数据
  "feedback": "审核通过"
}
```

**响应**:
```json
{
  "thread_id": "workflow_1_a3f2c9d1",
  "status": "completed",
  "new_usercase_id": "UC_12345",
  "created_case": {...}
}
```

### 3. 查询工作流状态

```bash
GET /api/v1/automation/workflow/workflow_1_a3f2c9d1/state
```

## 前端使用

### 1. 填写表单

- 用例名称、模块 ID、场景 ID（必填）
- 测试步骤、预期结果（建议填写）
- 优先级、测试类型（可选）

### 2. 启动工作流

点击"启动工作流"按钮，系统会：
- 调用后端 API 启动工作流
- 显示流程步骤进度
- 如果需要审核，自动弹出审核界面

### 3. 人工审核

如果数据校验发现问题，会弹出审核界面：

- 🔍 查看校验结果汇总
- ⚠️ 查看每条数据的错误详情
- ✏️ 在线编辑修正字段值
- 🏷️ 点击枚举值标签快速填入
- ✅ 确认提交或拒绝重新生成

### 4. 完成

- 显示成功结果
- 提供"查看用例"和"创建新用例"按钮

## 核心优势

### 1. 状态持久化

- 使用 SQLite 保存检查点
- 支持暂停和恢复
- 断电/崩溃后可恢复

### 2. 人工审核（Human-in-the-Loop）

- 工作流自动暂停在审核节点
- 前端实时显示审核界面
- 支持在线编辑和修正
- 三种审核结果：通过/修改/拒绝

### 3. 智能数据校验

- **枚举值校验**：确保值在有效范围内
- **联动规则校验**：确保字段间依赖关系正确
- **必填字段校验**：确保必填字段已填写
- **详细错误报告**：每个错误都有修正建议

### 4. 自动重试机制

- 生成失败自动重试，最多 3 次
- 每次重试都会记录重试次数
- 超过限制后标记为失败

### 5. 条件分支决策

- 根据校验结果自动决定下一步
- 支持循环和分支控制
- 灵活的流程编排

## 故障排查

### 问题 1: 工作流启动失败

**可能原因**:
- 自动化平台 API 不可用
- 场景 ID 不存在
- 数据库连接失败

**解决方法**:
1. 检查自动化平台 API 地址配置
2. 验证场景 ID 是否存在
3. 检查数据库连接

### 问题 2: AI 生成失败

**可能原因**:
- AI 服务未配置
- API Key 无效
- 网络超时

**解决方法**:
1. 检查 AI 服务配置（模型配置页面）
2. 验证 API Key 是否有效
3. 检查网络连接

### 问题 3: 人工审核界面不显示

**可能原因**:
- 前端状态未更新
- WebSocket 连接断开

**解决方法**:
1. 刷新页面重试
2. 检查浏览器控制台错误
3. 查看后端日志

### 问题 4: 数据校验过严

**可能原因**:
- 字段元数据配置错误
- 枚举值不完整

**解决方法**:
1. 检查自动化平台的字段元数据 API
2. 暂时跳过校验（修改代码）
3. 联系平台方更新元数据

## 开发调试

### 查看工作流日志

```bash
# 后端日志
tail -f backend/logs/app.log

# 工作流详细日志
# 所有日志都会打印 [工作流] 前缀
```

### 查看检查点数据库

```bash
# 安装 SQLite 客户端
# Windows: 下载 sqlite3.exe
# Mac: brew install sqlite3

# 查询检查点
sqlite3 backend/data/checkpoints/automation_workflow.db

# SQL 查询
SELECT * FROM checkpoints;
```

### 调试模式

```python
# 在 automation_workflow_service.py 中
# 所有节点都有详细的 print 日志
# 可以查看每个节点的输入输出
```

## 注意事项

1. **线程 ID 唯一性**: 每次启动工作流都会生成唯一的 thread_id
2. **检查点有效期**: 检查点会永久保存，建议定期清理
3. **并发限制**: 同一用户同时只能有一个工作流在执行
4. **网络超时**: AI 调用有超时保护，最长 180 秒
5. **数据安全**: 审核界面的数据仅在前端修改，提交后才更新

## 后续优化建议

1. ✅ 添加工作流历史记录查询
2. ✅ 支持批量创建用例
3. ✅ 添加工作流暂停/恢复接口
4. ✅ 优化前端交互体验
5. ✅ 添加数据校验规则配置界面
