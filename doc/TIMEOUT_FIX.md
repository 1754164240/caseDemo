# OpenAI API 超时问题修复指南

## 📋 问题描述
生成测试点或测试用例时出现 `Request timed out` 错误。

## ✅ 已完成的修复

### 1. 增加超时时间
- **原值**: 30 秒
- **新值**: 180 秒（3 分钟）
- **位置**: `app/core/config.py` 第 44 行

### 2. 改进日志输出
- 显示每次尝试的耗时
- 显示错误类型和详细信息
- 显示配置参数（超时时间、重试次数等）

### 3. 完善重试机制
- 测试点提取：3 次重试
- 测试用例生成：3 次重试
- 每次重试间隔：2 秒

## 🚀 使用方法

### 步骤 1: 重启后端服务（必需）

**重要**: 配置修改后必须重启服务才能生效！

```bash
# 停止当前运行的服务（Ctrl+C）

# 重新启动服务
cd D:\caseDemo1\backend
python main.py
```

### 步骤 2: 检查启动日志

服务启动时会显示配置信息：
```
[INFO] 初始化 AI 服务 - 模型: gpt-4, 超时: 180秒, 温度: 0.7, 最大重试: 3次
```

确认超时时间显示为 **180秒**。

### 步骤 3: 测试功能

尝试生成测试点或测试用例，观察日志：

```
[INFO] 调用 OpenAI API 提取测试点...
[INFO] 配置信息 - 超时: 180秒, 最大重试: 3次
[INFO] 第 1/3 次尝试...
[INFO] API 调用成功，耗时: 45.23秒
```

## 🔧 进一步优化（可选）

### 如果仍然超时，可以继续增加超时时间：

编辑 `app/core/config.py` 第 44 行：

```python
AI_REQUEST_TIMEOUT: int = 300  # 改为 5 分钟
```

### 或创建 `.env` 文件自定义配置：

```env
# 在 backend 目录下创建 .env 文件
AI_REQUEST_TIMEOUT=300
AI_MAX_RETRIES=5
AI_RETRY_INTERVAL=3.0
```

## 📊 性能建议

1. **网络优化**
   - 使用稳定的网络连接
   - 如果使用代理，确保代理稳定

2. **API 优化**
   - 检查 API Key 是否有效
   - 确认 API Base URL 配置正确
   - 考虑使用更快的模型（如 gpt-3.5-turbo）

3. **输入优化**
   - 测试点提取：限制需求文档长度（当前最大 120,000 字符）
   - 测试用例生成：每个测试点生成 2-3 个用例

## 🐛 故障排查

### 问题：启动后仍显示 30 秒超时
**解决**: 确保已重启服务，检查是否有多个服务实例在运行

### 问题：所有重试都失败
**可能原因**:
1. API Key 无效或过期
2. API Base URL 配置错误
3. 网络连接问题
4. API 配额用尽

**检查方法**:
```python
# 在 Python 中测试 API 连接
from openai import OpenAI
client = OpenAI(api_key="your-key", base_url="your-base-url")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
    timeout=180
)
print(response)
```

### 问题：第一次超时，第二次成功
**正常现象**: 这是重试机制在工作，说明配置正确

## 📞 需要帮助？

如果问题持续存在，请提供以下信息：
1. 完整的错误日志
2. 启动时的配置信息
3. 使用的模型名称
4. API Base URL（隐藏敏感信息）

