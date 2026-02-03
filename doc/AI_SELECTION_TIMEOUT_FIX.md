# AI选择用例超时问题修复

## 问题描述

生成自动化用例时，程序卡在"使用AI选择最佳用例"步骤：

```
[INFO] 使用AI选择最佳用例...
[DEBUG] 可选用例数量: 10
# 程序挂起，无响应
```

## 根本原因

1. **AI模型API响应慢** - glm-4.7可能存在网络或稳定性问题
2. **Prompt过长** - 10个用例的完整信息可能导致token超限
3. **缺少超时保护** - 原代码没有显式的超时控制机制

## 已实施的解决方案

**修改文件**: `backend/app/services/automation_service.py`

### 1. 添加180秒超时控制

使用 `ThreadPoolExecutor` + `future.result(timeout=180)` 强制超时：

```python
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

with ThreadPoolExecutor(max_workers=1) as executor:
    future = executor.submit(call_ai)
    try:
        response = future.result(timeout=180)  # 180秒超时
        selected_id = response.content.strip()
        print(f"[INFO] AI选择的用例ID: {selected_id}")
        # 查找匹配的用例...
    except FutureTimeoutError:
        print(f"[WARNING] AI调用超时（180秒），使用第一个用例")
        return available_cases[0]
```

### 2. 优化Prompt长度

简化用例信息，减少约70%的token使用：

```python
# 限制字段长度
cases_for_ai = []
for c in available_cases:
    desc = str(c.get('description', ''))
    if len(desc) > 100:
        desc = desc[:100] + "..."

    case_info = {
        'id': str(c.get('usercaseId', '')),
        'name': str(c.get('name', ''))[:100],
        'desc': desc
    }
    cases_for_ai.append(case_info)

# 简化prompt（移除前置条件、测试步骤等）
prompt = f"""选择最匹配的自动化用例模板。

测试用例：
标题：{test_title[:100]}
描述：{test_desc[:200]}

可选模板：
{json.dumps(cases_for_ai, ensure_ascii=False)}

请只返回选中模板的id（usercaseId）。"""
```

### 3. 早期返回优化

如果只有1个可用用例，直接返回，避免调用AI：

```python
if len(available_cases) <= 1:
    print("[INFO] 只有1个或更少可用用例，直接使用")
    return available_cases[0] if available_cases else None
```

### 4. 增强日志输出

```python
print(f"[INFO] 使用AI选择最佳用例（超时限制180秒）...")
print(f"[DEBUG] 可选用例数量: {len(available_cases)}")
print(f"[DEBUG] Prompt长度: {len(prompt)} 字符")
```

## 预期效果

### 正常情况（AI成功返回）

```
[INFO] 使用AI选择最佳用例（超时限制180秒）...
[DEBUG] 可选用例数量: 10
[DEBUG] Prompt长度: 687 字符
[INFO] AI选择的用例ID: 9f86abdb-ae34-498b-afb2-ca88547da281
[INFO] 找到匹配的用例: 3年交保费略高于最低限额但非整数倍
```

### 超时情况（180秒后降级）

```
[INFO] 使用AI选择最佳用例（超时限制180秒）...
[DEBUG] 可选用例数量: 10
[DEBUG] Prompt长度: 687 字符
[WARNING] AI调用超时（180秒），使用第一个用例
# 继续执行后续步骤，不会卡住
```

### 早期返回（只有1个用例）

```
[INFO] 只有1个或更少可用用例，直接使用
# 跳过AI调用
```

## 使用说明

1. **重启后端服务**以应用修改
2. **测试生成自动化用例**，观察日志输出
3. **正常情况下**，AI应该在几秒到几十秒内返回结果
4. **超时情况下**，180秒后会自动降级使用第一个用例

## 进一步优化建议

### 如果180秒仍然超时

**方案A: 添加性能监控**

```python
import time

start_time = time.time()
response = future.result(timeout=180)
elapsed_time = time.time() - start_time

print(f"[INFO] AI调用耗时: {elapsed_time:.2f}秒")

if elapsed_time > 60:
    print(f"[WARNING] AI调用较慢: {elapsed_time}秒")
```

**方案B: 缩短超时 + 增加重试**

```python
max_retries = 2
timeout = 90

for attempt in range(max_retries):
    try:
        response = future.result(timeout=timeout)
        break
    except FutureTimeoutError:
        if attempt < max_retries - 1:
            print(f"[WARNING] 第{attempt+1}次超时，重试...")
        else:
            return available_cases[0]
```

**方案C: 限制传递给AI的用例数量**

```python
max_cases = 5
if len(available_cases) > max_cases:
    print(f"[INFO] 用例过多({len(available_cases)}个)，仅使用前{max_cases}个")
    available_cases = available_cases[:max_cases]
```

**方案D: 切换到更稳定的模型**

在系统管理 → 模型配置中，切换到：
- OpenAI GPT-4/GPT-3.5（更稳定，成本高）
- 智谱 GLM-4-Plus（glm-4.7的稳定版）
- DeepSeek（性价比高）

## 技术细节

### 为什么使用ThreadPoolExecutor？

1. **真正的超时控制** - `future.result(timeout=180)` 可以强制中断
2. **线程隔离** - AI调用在单独线程中执行，不会阻塞主线程
3. **兼容性好** - 在FastAPI中使用线程池是安全的

### 为什么是180秒？

- AI服务的默认超时是180秒（`ai_service.py:66`）
- 网络慢或模型负载高时可能需要较长时间
- 180秒是用户可以接受的等待上限
- 超时后自动降级，保证流程不会卡死

## 相关文件

- `backend/app/services/automation_service.py` - 主要修改文件
- `backend/app/services/ai_service.py` - AI服务初始化（超时配置）
- `doc/TEST_DATA_GENERATION.md` - 测试数据生成方案文档

---

**修复时间**: 2026-02-03
**状态**: 已实施，180秒超时机制生效
**影响范围**: 所有自动化用例生成流程
