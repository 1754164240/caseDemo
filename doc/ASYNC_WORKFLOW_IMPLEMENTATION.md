# 异步工作流系统实现说明

## 概述

将自动化用例生成工作流改造为异步执行模式，解决工作流执行时间过长导致前端等待的问题。

## 架构设计

### 核心组件

1. **WorkflowTask 模型** (`app/models/workflow_task.py`)
   - 记录工作流任务状态
   - 支持进度跟踪（0-100%）
   - 存储执行结果和错误信息

2. **异步执行器** (`app/services/async_workflow_executor.py`)
   - 后台线程执行工作流
   - 实时更新任务状态
   - 集成 WebSocket 推送进度

3. **API 接口** (`app/api/v1/endpoints/automation_workflow.py`)
   - 启动异步工作流
   - 查询任务状态
   - 提交人工审核

## 工作流执行流程

### 1. 启动阶段（立即返回）

```
前端点击"生成自动化用例"
  ↓
POST /api/v1/automation/workflow/start
  ↓
创建 WorkflowTask 记录（status: pending）
  ↓
启动后台线程执行工作流
  ↓
立即返回 { task_id, thread_id }
```

**响应时间**: < 500ms

### 2. 后台执行阶段

```
后台线程执行 10 步工作流
  ↓
每完成一步更新进度
  ↓
通过 WebSocket 推送实时进度
  ↓
执行到步骤9（人工审核）时暂停
  ↓
更新 status: reviewing
  ↓
推送审核通知到前端
```

**执行时间**: 1-3 分钟（取决于 AI 调用速度）

### 3. 人工审核阶段

```
前端收到 WebSocket 通知
  ↓
显示审核弹窗
  ↓
用户审核数据
  ↓
POST /api/v1/automation/workflow/{thread_id}/review
  ↓
继续执行工作流
  ↓
创建自动化用例
  ↓
更新 status: completed
```

## API 接口说明

### 1. 启动工作流

**请求**:
```http
POST /api/v1/automation/workflow/start
Content-Type: application/json

{
  "test_case_id": 123,
  "name": "自动化用例名称",
  "module_id": "1",
  "scene_id": "SC001"
}
```

**响应**:
```json
{
  "task_id": 456,
  "thread_id": "workflow_1_abc123",
  "status": "pending",
  "message": "工作流已启动，正在后台执行...",
  "test_case_id": 123
}
```

### 2. 查询任务状态

**请求**:
```http
GET /api/v1/automation/workflow/tasks/456
```

**响应**:
```json
{
  "id": 456,
  "thread_id": "workflow_1_abc123",
  "status": "reviewing",
  "current_step": "awaiting_human_review",
  "progress": 80,
  "need_review": true,
  "interrupt_data": {
    "generated_body": [...],
    "validation_result": {...}
  },
  "created_at": "2026-02-05T10:30:00Z",
  "started_at": "2026-02-05T10:30:05Z"
}
```

### 3. 查询任务列表

**请求**:
```http
GET /api/v1/automation/workflow/tasks?status=reviewing&limit=10
```

**响应**:
```json
{
  "total": 25,
  "items": [
    {
      "id": 456,
      "status": "reviewing",
      "progress": 80,
      "test_case_id": 123,
      "created_at": "2026-02-05T10:30:00Z"
    }
  ],
  "limit": 10,
  "offset": 0
}
```

### 4. 提交审核

**请求**:
```http
POST /api/v1/automation/workflow/workflow_1_abc123/review
Content-Type: application/json

{
  "review_status": "approved",
  "corrected_body": null,
  "feedback": "数据正确"
}
```

**响应**:
```json
{
  "thread_id": "workflow_1_abc123",
  "status": "completed",
  "current_step": "case_created",
  "new_usercase_id": "UC789",
  "created_case": {...}
}
```

## WebSocket 实时通知

### 消息类型

1. **workflow_started**
```json
{
  "type": "workflow_started",
  "data": {
    "thread_id": "workflow_1_abc123",
    "status": "processing",
    "message": "工作流已启动，正在执行..."
  }
}
```

2. **workflow_need_review**
```json
{
  "type": "workflow_need_review",
  "data": {
    "thread_id": "workflow_1_abc123",
    "status": "reviewing",
    "message": "AI已生成测试数据，请进行人工审核",
    "interrupt_data": {...},
    "generated_body": [...]
  }
}
```

3. **workflow_failed**
```json
{
  "type": "workflow_failed",
  "data": {
    "thread_id": "workflow_1_abc123",
    "status": "failed",
    "error": "错误信息"
  }
}
```

## 任务状态说明

| 状态 | 说明 | 进度 |
|------|------|------|
| `pending` | 已创建，等待执行 | 0% |
| `processing` | 正在执行中 | 5-80% |
| `reviewing` | 等待人工审核 | 80% |
| `completed` | 执行成功 | 100% |
| `failed` | 执行失败 | 0% |

## 数据库部署

### 1. 创建表

```bash
cd backend
python -m scripts.create_workflow_tasks_table
```

### 2. 表结构

```sql
CREATE TABLE workflow_tasks (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR(100) UNIQUE NOT NULL,
    task_type VARCHAR(50) DEFAULT 'automation_case',
    user_id INTEGER NOT NULL REFERENCES users(id),
    test_case_id INTEGER REFERENCES test_cases(id),
    status VARCHAR(50) DEFAULT 'pending',
    current_step VARCHAR(100),
    progress INTEGER DEFAULT 0,
    input_params JSON,
    result_data JSON,
    error_message TEXT,
    need_review BOOLEAN DEFAULT FALSE,
    interrupt_data JSON,
    new_usercase_id VARCHAR(100),
    created_case JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_workflow_tasks_thread_id ON workflow_tasks(thread_id);
CREATE INDEX idx_workflow_tasks_user_id ON workflow_tasks(user_id);
CREATE INDEX idx_workflow_tasks_status ON workflow_tasks(status);
```

## 前端集成建议

### 1. 启动工作流

```typescript
// 点击生成按钮
const handleGenerate = async () => {
  const response = await api.post('/automation/workflow/start', {
    test_case_id: 123,
    name: '自动化用例',
    module_id: '1',
    scene_id: 'SC001'
  });

  const { task_id, thread_id } = response.data;

  // 跳转到任务列表或显示进度
  navigate(`/automation/tasks/${task_id}`);
};
```

### 2. 轮询查询状态

```typescript
useEffect(() => {
  const timer = setInterval(async () => {
    const response = await api.get(`/automation/workflow/tasks/${taskId}`);
    const task = response.data;

    setProgress(task.progress);
    setStatus(task.status);

    if (task.status === 'reviewing') {
      // 显示审核弹窗
      setShowReviewModal(true);
      clearInterval(timer);
    } else if (task.status === 'completed' || task.status === 'failed') {
      clearInterval(timer);
    }
  }, 3000); // 每3秒查询一次

  return () => clearInterval(timer);
}, [taskId]);
```

### 3. WebSocket 实时更新（推荐）

```typescript
useEffect(() => {
  const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/${userId}?token=${token}`);

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    if (message.type === 'workflow_need_review') {
      setShowReviewModal(true);
      setReviewData(message.data);
    } else if (message.type === 'workflow_failed') {
      notification.error({ message: message.data.error });
    }
  };

  return () => ws.close();
}, [userId]);
```

## 性能优化

### 1. 数据库索引

已创建索引：
- `thread_id` (唯一查询)
- `user_id` (列表查询)
- `status` (状态筛选)

### 2. 任务清理

建议定期清理历史任务（>30天）：

```python
# 定时任务
def cleanup_old_tasks():
    from datetime import datetime, timedelta
    threshold = datetime.now() - timedelta(days=30)

    db.query(WorkflowTask).filter(
        WorkflowTask.created_at < threshold,
        WorkflowTask.status.in_(['completed', 'failed'])
    ).delete()
    db.commit()
```

### 3. 进度推送优化

- 使用 WebSocket 代替轮询
- 减少数据库查询频率
- 进度更新批量提交

## 监控指标

建议监控以下指标：

1. **任务成功率**: `completed / (completed + failed)`
2. **平均执行时间**: `avg(completed_at - started_at)`
3. **人工审核通过率**: `approved / total_reviews`
4. **任务积压数量**: `count(status = 'pending')`

## 故障排查

### 1. 任务一直 pending

**原因**: 后台线程未启动
**解决**: 检查日志，确认 `start_workflow_background` 被调用

### 2. 任务卡在 processing

**原因**: 工作流执行异常但未捕获
**解决**: 查看 `error_message` 字段，检查工作流日志

### 3. WebSocket 未收到通知

**原因**: WebSocket 连接断开或用户ID不匹配
**解决**: 检查连接状态，验证 `user_id` 参数

## 后续优化建议

1. **使用消息队列** (Celery + Redis)
   - 更可靠的任务调度
   - 支持任务重试
   - 分布式执行

2. **持久化工作流状态**
   - 使用 SqliteSaver 代替 MemorySaver
   - 服务器重启后任务可恢复

3. **添加任务优先级**
   - 支持紧急任务优先执行
   - 避免长时间等待

4. **任务执行监控**
   - Prometheus 指标收集
   - Grafana 可视化面板
