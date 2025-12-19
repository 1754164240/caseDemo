# 修复 StructuredTool 调用错误

**错误信息**：`TypeError: 'StructuredTool' object is not callable`

**日期**：2024-12-18

---

## 🐛 问题描述

在AI生成测试数据时，调用 `agent_chat` 方法出现以下错误：

```
[ERROR] AI生成测试数据失败: TypeError: 'StructuredTool' object is not callable
Traceback (most recent call last):
  File "D:\caseDemo1\backend\app\services\automation_service.py", line 495, in generate_case_body_by_ai
    response = ai_service.agent_chat(prompt)
  File "D:\caseDemo1\backend\app\services\ai_service.py", line 157, in agent_chat
    time_context = self._maybe_get_time_context(prompt)
  File "D:\caseDemo1\backend\app\services\ai_service.py", line 192, in _maybe_get_time_context       
    current_dt = current_datetime_tool()
TypeError: 'StructuredTool' object is not callable
```

---

## 🔍 问题原因

### LangChain Tool 装饰器

在 `app/tools/date_tools.py` 中，时间工具使用 `@tool` 装饰器定义：

```python
from langchain.tools import tool

@tool("current_date")
def current_date_tool() -> str:
    """返回当前日期（东八区），格式为 YYYY-MM-DD"""
    return datetime.now(CN_TZ).strftime("%Y-%m-%d")

@tool("current_datetime")
def current_datetime_tool() -> str:
    """返回当前日期和时间（东八区），格式为 YYYY-MM-DD HH:MM:SS"""
    return datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M:%S")
```

**关键点**：
- `@tool` 装饰器会将函数包装成 `StructuredTool` 对象
- `StructuredTool` 不能像普通函数一样直接调用 `tool()`
- 必须使用 `.invoke()` 或 `.run()` 方法来执行

### 错误的调用方式

在 `ai_service.py` 中：

```python
def _maybe_get_time_context(self, prompt: str) -> str:
    if any(k in lower for k in keywords):
        # ❌ 错误：直接调用 StructuredTool 对象
        current_dt = current_datetime_tool()
        current_d = current_date_tool()
        return f"当前日期（东八区）：{current_d}，当前时间（东八区）：{current_dt}。"
    return ""
```

---

## ✅ 解决方案

### 使用 .invoke() 方法调用

LangChain 的 `StructuredTool` 对象需要使用 `.invoke()` 方法：

```python
def _maybe_get_time_context(self, prompt: str) -> str:
    """简单检测是否需要时间信息，必要时主动调用工具避免模型忽略工具"""
    lower = prompt.lower()
    keywords = ["date", "time", "today", "now", "日期", "时间", "今天", "几点", "几号"]
    if any(k in lower for k in keywords):
        # ✅ 正确：使用 .invoke() 方法调用
        current_dt = current_datetime_tool.invoke({})
        current_d = current_date_tool.invoke({})
        return f"当前日期（东八区）：{current_d}，当前时间（东八区）：{current_dt}。"
    return ""
```

**说明**：
- `.invoke({})` 接受一个字典参数（工具的输入）
- 对于这些不需要参数的工具，传入空字典 `{}`
- 返回值是工具执行的结果（字符串）

---

## 📋 修改文件

- ✅ `backend/app/services/ai_service.py` - 修复 `_maybe_get_time_context` 方法

---

## 🔄 LangChain Tool 调用方式

### 方式1：.invoke() 方法（推荐）

```python
from langchain.tools import tool

@tool("my_tool")
def my_tool_function(param: str) -> str:
    """工具描述"""
    return f"结果: {param}"

# ✅ 正确调用
result = my_tool_function.invoke({"param": "value"})

# ❌ 错误调用
result = my_tool_function("value")  # TypeError
```

### 方式2：.run() 方法

```python
# 也可以使用 .run() 方法
result = my_tool_function.run({"param": "value"})
```

### 方式3：直接使用原始函数

如果不需要工具的元数据和LangChain集成，可以直接使用底层函数：

```python
from datetime import datetime, timezone, timedelta

CN_TZ = timezone(timedelta(hours=8))

# 直接使用 datetime，不依赖工具包装
current_date = datetime.now(CN_TZ).strftime("%Y-%m-%d")
current_datetime = datetime.now(CN_TZ).strftime("%Y-%m-%d %H:%M:%S")
```

---

## 🚀 验证修复

### 1. 重启后端服务

```bash
cd backend
python main.py
```

### 2. 测试AI生成功能

点击"自动化"按钮，观察日志：

### 修复前（错误）

```bash
[INFO] 调用AI生成测试数据（基于31个字段）
[DEBUG] ========== AI Prompt 结束 ==========
❌ [ERROR] AI生成测试数据失败: TypeError: 'StructuredTool' object is not callable
```

### 修复后（正常）

```bash
[INFO] 调用AI生成测试数据（基于31个字段）
[DEBUG] ========== AI Prompt 开始 ==========
...
[DEBUG] ========== AI Prompt 结束 ==========
[DEBUG] ========== AI Response 开始 ==========
...
[DEBUG] ========== AI Response 结束 ==========
✅ [INFO] ✅ AI生成了 2 条测试数据
[INFO] ✅ 已将AI生成的 2 条测试数据添加到caseDefine
```

---

## 📚 相关知识

### LangChain Tools 概念

**什么是 Tool？**
- Tool 是 LangChain 中可以被 Agent 调用的函数
- 使用 `@tool` 装饰器将普通函数转换为 LangChain Tool
- Tool 包含函数逻辑、参数定义、描述等元数据

**为什么使用 Tool？**
- Agent 可以理解工具的功能描述
- 自动生成参数模式
- 统一的调用接口
- 便于与 LLM 集成

**Tool vs 普通函数**

| 特性 | 普通函数 | LangChain Tool |
|------|---------|---------------|
| 调用方式 | `func(arg)` | `tool.invoke({"arg": value})` |
| 元数据 | 无 | 有（名称、描述、参数模式） |
| Agent集成 | 需手动处理 | 自动集成 |
| 类型检查 | 依赖类型提示 | 自动验证输入 |

---

## 💡 最佳实践

### 1. 明确工具的调用场景

**Agent 调用**（自动）：
```python
# Agent 会自动使用 .invoke() 调用工具
agent_executor.invoke({"messages": [{"role": "user", "content": "今天几号？"}]})
```

**手动调用**（需要显式使用 .invoke()）：
```python
# 在代码中直接调用工具
result = current_date_tool.invoke({})
```

### 2. 无参数工具的调用

```python
@tool("no_params_tool")
def no_params_tool() -> str:
    """不需要参数的工具"""
    return "result"

# ✅ 传入空字典
result = no_params_tool.invoke({})
```

### 3. 有参数工具的调用

```python
@tool("params_tool")
def params_tool(name: str, age: int) -> str:
    """需要参数的工具"""
    return f"{name} is {age} years old"

# ✅ 传入参数字典
result = params_tool.invoke({"name": "Alice", "age": 30})
```

---

## 🔗 相关文档

- [AI生成测试数据功能](./AI_GENERATE_BODY_DATA.md)
- [v1.3.6 更新摘要](./UPDATE_v1.3.6_SUMMARY.md)
- [LangChain Tools 文档](https://python.langchain.com/docs/modules/tools/)

---

## 🎓 经验教训

1. **装饰器会改变对象类型**
   - `@tool` 装饰器将函数包装成 `StructuredTool` 对象
   - 需要了解包装后的对象如何使用

2. **查看错误堆栈**
   - 堆栈清楚显示了问题在哪里（`current_datetime_tool()`）
   - 错误类型明确（`'StructuredTool' object is not callable`）

3. **阅读源代码**
   - 查看 `date_tools.py` 发现使用了 `@tool` 装饰器
   - 了解工具的定义方式

4. **参考文档**
   - LangChain 文档说明了 Tool 的正确调用方式
   - 使用 `.invoke()` 方法而不是直接调用

---

**修复版本**：v1.3.6.2  
**修复日期**：2024-12-18  
**修复类型**：Bug修复


