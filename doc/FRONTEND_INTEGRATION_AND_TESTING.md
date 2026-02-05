# 异步工作流系统 - 前端集成与测试验证指南

## ✅ 已完成的工作

### 1. 后端实现
- ✅ WorkflowTask 数据模型
- ✅ 异步执行器（后台线程）
- ✅ API 接口（启动、查询、审核）
- ✅ WebSocket 实时推送
- ✅ 数据库表创建

### 2. 前端实现
- ✅ API 服务集成 (`workflowTasksAPI`)
- ✅ 任务列表页面 (`WorkflowTasks.tsx`)
- ✅ WebSocket 消息处理
- ✅ 路由配置

---

## 🚀 测试验证步骤

### 步骤1: 启动后端服务

```bash
cd backend
python -m scripts.main
```

**验证点**：
- 后端服务在 `http://localhost:8000` 启动
- 查看日志确认数据库连接成功
- 确认 WebSocket 端点可用

### 步骤2: 启动前端服务

```bash
cd frontend
npm run dev
```

**验证点**：
- 前端服务在 `http://localhost:5173` 启动
- 浏览器自动打开登录页面

### 步骤3: 登录系统

访问 `http://localhost:5173` 并登录

**测试账号**（如果没有，需要先创建）：
```bash
cd backend
python -m scripts.create_test_user
```

### 步骤4: 测试异步工作流

#### 4.1 查看任务列表

1. 访问 `http://localhost:5173/automation/workflow/tasks`
2. **验证点**：
   - ✅ 页面正常加载
   - ✅ 显示任务列表表格
   - ✅ 显示筛选和刷新按钮
   - ✅ 显示"自动刷新: 每 5 秒"提示

#### 4.2 启动新的工作流任务

**方法1: 通过 API 测试**

```bash
# 使用 curl 测试
curl -X POST http://localhost:8000/api/v1/automation/workflow/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "test_case_id": 1,
    "name": "测试自动化用例",
    "module_id": "1",
    "scene_id": "SC001"
  }'
```

**预期响应**：
```json
{
  "task_id": 1,
  "thread_id": "workflow_1_abc123",
  "status": "pending",
  "message": "工作流已启动，正在后台执行...",
  "test_case_id": 1
}
```

**方法2: 通过前端测试**

如果有现有的测试用例页面，可以从那里触发生成自动化用例。

#### 4.3 观察任务执行过程

1. 在任务列表页面观察任务状态变化
2. **验证点**：
   - ✅ 任务从 `pending` 变为 `processing`
   - ✅ 进度条从 0% 逐渐增加
   - ✅ 当前步骤显示变化（如：`test_case_loaded` → `scenario_matched` → ...）
   - ✅ 页面每 5 秒自动刷新

#### 4.4 WebSocket 实时通知测试

**打开浏览器控制台**，观察 WebSocket 消息：

```javascript
// 控制台应该显示
WebSocket connected
```

**验证点**：
- ✅ 工作流启动时收到通知消息
- ✅ 需要审核时弹出提示
- ✅ 执行失败时显示错误消息

#### 4.5 查看任务详情

1. 点击任务列表中的"详情"按钮
2. **验证点**：
   - ✅ 弹出详情模态框
   - ✅ 显示任务ID、Thread ID
   - ✅ 显示状态和进度
   - ✅ 显示当前步骤
   - ✅ 显示输入参数（JSON格式）
   - ✅ 如果有错误，显示错误信息

#### 4.6 人工审核流程测试

当任务状态变为 `reviewing` 时：

1. **验证点**：
   - ✅ 任务列表中出现"审核"按钮
   - ✅ 状态标签显示"等待审核"（橙色）
   - ✅ 进度条显示 80%
   - ✅ WebSocket 推送审核通知

2. 点击"审核"按钮
3. **验证点**：
   - ✅ 显示确认对话框
   - ✅ 显示 Thread ID

#### 4.7 任务筛选测试

1. 使用状态筛选下拉框
2. **验证点**：
   - ✅ 选择"等待执行"只显示 pending 任务
   - ✅ 选择"执行中"只显示 processing 任务
   - ✅ 选择"等待审核"只显示 reviewing 任务
   - ✅ 选择"已完成"只显示 completed 任务
   - ✅ 选择"失败"只显示 failed 任务

#### 4.8 分页功能测试

1. 创建多个任务（>20个）
2. **验证点**：
   - ✅ 显示分页控件
   - ✅ 显示总数（如"共 25 条"）
   - ✅ 可以切换页码
   - ✅ 可以修改每页显示数量
   - ✅ 快速跳转功能正常

---

## 📊 完整测试用例

### 测试用例1: 正常流程（成功完成）

**步骤**：
1. 启动工作流任务
2. 等待自动执行到审核阶段
3. 提交审核（通过）
4. 等待创建自动化用例

**预期结果**：
- 状态: `pending` → `processing` → `reviewing` → `processing` → `completed`
- 进度: 0% → 5% → 80% → 85% → 100%
- `new_usercase_id` 有值

### 测试用例2: 审核拒绝（重新生成）

**步骤**：
1. 启动工作流任务
2. 等待到审核阶段
3. 提交审核（拒绝）
4. 观察重新生成

**预期结果**：
- 状态回到 `processing`
- 重新执行 AI 生成数据
- 再次进入审核状态

### 测试用例3: 执行失败

**步骤**：
1. 使用不存在的 test_case_id 启动工作流
2. 观察任务状态

**预期结果**：
- 状态变为 `failed`
- `error_message` 显示错误原因
- 进度归零

### 测试用例4: 并发任务

**步骤**：
1. 同时启动 5 个工作流任务
2. 观察任务列表

**预期结果**：
- 所有任务都正常执行
- 互不干扰
- 状态独立更新

### 测试用例5: WebSocket 断线重连

**步骤**：
1. 启动工作流任务
2. 断开网络
3. 恢复网络
4. 观察 WebSocket 状态

**预期结果**：
- WebSocket 自动重连
- 继续接收实时通知
- 任务正常完成

---

## 🔍 性能测试

### 响应时间测试

| 操作 | 预期响应时间 |
|------|------------|
| 启动工作流 | < 500ms |
| 查询任务状态 | < 200ms |
| 查询任务列表 | < 500ms |
| 提交审核 | < 300ms |
| 工作流完整执行 | 1-3 分钟 |

### 负载测试

- 同时处理 10 个工作流任务
- 任务列表支持 1000+ 条记录
- WebSocket 支持 100+ 并发连接

---

## 🐛 常见问题排查

### 问题1: 任务一直 pending

**症状**：任务创建后一直处于 pending 状态

**排查**：
1. 检查后端日志，确认后台线程是否启动
2. 查看数据库 `workflow_tasks` 表，检查 `started_at` 字段
3. 检查是否有异常抛出

**解决**：
- 重启后端服务
- 检查 `async_workflow_executor.py` 的线程启动逻辑

### 问题2: WebSocket 未收到通知

**症状**：任务执行但前端没有实时通知

**排查**：
1. 浏览器控制台查看 WebSocket 连接状态
2. 检查 `wsService.connect(userId)` 是否被调用
3. 查看后端 WebSocket 日志

**解决**：
- 确认 `userId` 正确
- 检查 token 是否有效
- 重新连接 WebSocket

### 问题3: 任务详情显示异常

**症状**：点击详情按钮报错或显示空数据

**排查**：
1. 检查 API 响应状态码
2. 查看浏览器 Network 面板
3. 确认任务 ID 是否正确

**解决**：
- 验证用户权限（是否有权查看该任务）
- 检查任务是否存在
- 刷新页面重试

### 问题4: 审核按钮不显示

**症状**：任务状态是 reviewing 但没有审核按钮

**排查**：
1. 检查 `need_review` 字段值
2. 检查 `interrupt_data` 是否存在
3. 查看前端条件渲染逻辑

**解决**：
- 确认后端正确设置了 `need_review = true`
- 检查工作流是否正确执行到 `human_review` 节点

---

## 📝 API 测试脚本

### Postman Collection

**创建 Postman Collection** 包含以下请求：

#### 1. 启动工作流
```
POST {{base_url}}/api/v1/automation/workflow/start
Headers:
  Authorization: Bearer {{token}}
  Content-Type: application/json
Body:
{
  "test_case_id": 1,
  "name": "测试自动化用例",
  "module_id": "1",
  "scene_id": "SC001"
}
```

#### 2. 查询任务状态
```
GET {{base_url}}/api/v1/automation/workflow/tasks/{{task_id}}
Headers:
  Authorization: Bearer {{token}}
```

#### 3. 查询任务列表
```
GET {{base_url}}/api/v1/automation/workflow/tasks?status=reviewing&limit=10
Headers:
  Authorization: Bearer {{token}}
```

#### 4. 提交审核
```
POST {{base_url}}/api/v1/automation/workflow/{{thread_id}}/review
Headers:
  Authorization: Bearer {{token}}
  Content-Type: application/json
Body:
{
  "review_status": "approved",
  "feedback": "数据正确"
}
```

---

## 🎯 验收标准

### 功能验收

- [ ] 可以成功启动工作流任务
- [ ] 任务列表正常显示和刷新
- [ ] WebSocket 实时通知正常工作
- [ ] 任务详情可以查看
- [ ] 人工审核流程完整
- [ ] 任务筛选和分页正常
- [ ] 错误处理正确

### 性能验收

- [ ] 启动工作流响应时间 < 500ms
- [ ] 任务列表加载时间 < 500ms
- [ ] 支持同时处理 10+ 任务
- [ ] WebSocket 稳定连接

### 用户体验验收

- [ ] 界面友好，操作直观
- [ ] 状态和进度显示清晰
- [ ] 错误提示明确
- [ ] 自动刷新流畅

---

## 🚀 部署检查清单

### 数据库
- [ ] 执行 `create_workflow_tasks_table.py` 脚本
- [ ] 验证表结构正确
- [ ] 验证外键约束

### 后端
- [ ] 更新 `requirements.txt` 依赖
- [ ] 重启后端服务
- [ ] 验证 API 端点可用
- [ ] 检查日志输出正常

### 前端
- [ ] 安装依赖（如果有新增）
- [ ] 构建生产版本
- [ ] 验证路由配置
- [ ] 检查 API 基础地址

---

## 📞 支持和反馈

遇到问题请提供：
1. 复现步骤
2. 错误截图
3. 浏览器控制台日志
4. 后端服务日志

详细文档参考：
- [后端实施文档](../doc/ASYNC_WORKFLOW_IMPLEMENTATION.md)
- [API 文档](http://localhost:8000/docs)
