# 自动化平台集成 - 故障排除指南

## 🐛 错误：Expecting value: line 1 column 1 (char 0)

### 错误说明

这个错误表示自动化测试平台的API返回的不是有效的JSON格式。

**完整错误信息：**
```
[ERROR] 创建自动化用例失败: 调用自动化平台失败: Expecting value: line 1 column 1 (char 0)
```

### 可能原因

1. **API地址配置错误**
   - 地址输入错误
   - 缺少协议（http:// 或 https://）
   - 端口号错误
   - 路径不正确

2. **API返回了非JSON内容**
   - 返回了HTML错误页面（404、500等）
   - 返回了空响应
   - 服务未正确实现JSON响应

3. **网络连接问题**
   - 无法访问目标服务器
   - 防火墙阻止
   - 服务未启动

4. **认证问题**
   - API需要认证但未提供
   - Token/API Key过期或无效

## 🔍 诊断步骤

### 步骤 1：运行诊断工具

我们提供了一个专门的诊断工具来测试连接：

```bash
cd backend
python test_automation_connection.py
```

诊断工具会：
- ✅ 检查配置是否存在
- ✅ 测试基础连接
- ✅ 测试创建用例接口
- ✅ 测试获取字段接口
- ✅ 显示详细的错误信息

**示例输出：**
```
============================================================
自动化测试平台连接诊断工具
============================================================

[步骤 1] 检查配置
✅ API地址已配置: http://192.168.1.100:8080

[步骤 2] 测试基础连接
✅ 可以连接到: http://192.168.1.100:8080
   状态码: 200
   Content-Type: text/html

[步骤 3] 测试创建用例接口
接口URL: http://192.168.1.100:8080/usercase/case/addCase
响应状态码: 404
响应内容:
<!DOCTYPE html>
<html>
<head><title>404 Not Found</title></head>
...

❌ 响应不是有效的JSON格式
   这通常意味着:
   1. API地址配置错误（可能返回了HTML错误页面）
   2. API未正确实现（应该返回JSON格式）
```

### 步骤 2：检查配置

#### 2.1 检查系统配置

1. 登录系统（管理员账号）
2. 进入"系统配置"→"第三方接入"
3. 检查"自动化测试平台 API 地址"

**正确格式：**
```
✅ http://192.168.1.100:8080
✅ https://autotest.example.com
✅ http://test-platform.local:9000

❌ 192.168.1.100:8080  (缺少协议)
❌ http://192.168.1.100:8080/  (末尾不要斜杠)
❌ http://192.168.1.100:8080/api  (不要包含具体路径)
```

#### 2.2 检查环境变量

查看 `backend/.env` 文件：

```bash
cat backend/.env | grep AUTOMATION_PLATFORM_API_BASE
```

应该看到：
```bash
AUTOMATION_PLATFORM_API_BASE=http://your-platform.com
```

### 步骤 3：手动测试API

使用 curl 或 Postman 手动测试API是否可用。

#### 测试基础连接

```bash
curl -v http://your-platform.com
```

**期望结果：**
- 能够连接
- 返回200或其他正常状态码

#### 测试创建用例接口

```bash
curl -X POST http://your-platform.com/usercase/case/addCase \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试用例",
    "moduleId": "test-module-id",
    "sceneId": "test-scene-id",
    "scenarioType": "API"
  }'
```

**期望返回：**
```json
{
  "success": true,
  "data": {
    "usercaseId": "...",
    "name": "测试用例",
    ...
  }
}
```

**如果返回HTML或其他内容：**
```html
<!DOCTYPE html>
<html>
  <head><title>404 Not Found</title></head>
  ...
```
说明API地址或路径不正确。

### 步骤 4：查看详细日志

现在后端服务会输出详细的调试信息。查看后端日志：

```bash
# 查看实时日志
tail -f backend.log

# 或查看最近的日志
tail -100 backend.log | grep -A 10 "调用自动化平台"
```

**日志示例：**
```
[INFO] 调用自动化平台创建用例
[INFO] URL: http://192.168.1.100:8080/usercase/case/addCase
[INFO] Payload: {'name': '测试用例', 'moduleId': 'xxx', ...}
[INFO] 响应状态码: 404
[INFO] 响应头: {'Content-Type': 'text/html', ...}
[INFO] 响应内容: <!DOCTYPE html>...
```

从日志可以看出：
- 实际调用的URL是什么
- 发送的数据是什么
- API返回的状态码和内容

## 🔧 解决方案

### 方案 1：API地址配置错误

**问题**：配置的地址不正确或格式错误

**解决**：
1. 确认正确的API地址
2. 在系统配置中更新为正确的地址
3. 格式：`http://域名:端口` （不要末尾斜杠）

**示例：**
```
错误: http://192.168.1.100:8080/api/
正确: http://192.168.1.100:8080
```

### 方案 2：API路径不匹配

**问题**：系统使用的API路径与实际不符

**系统使用的路径：**
- 创建用例：`/usercase/case/addCase`
- 获取字段：`/api/automation/bom/variable/{sceneId}/{usercaseId}`

**解决**：
1. 确认自动化平台的实际API路径
2. 如果路径不同，需要调整：

**临时方案：** 调整系统配置的API地址，包含基础路径
```
例如，如果实际接口是：
http://platform.com/api/v1/usercase/case/addCase

则配置：
http://platform.com/api/v1
```

**永久方案：** 修改代码中的路径（如果需要）

### 方案 3：网络连接问题

**问题**：无法访问自动化平台

**诊断**：
```bash
# 测试网络连通性
ping your-platform.com

# 测试端口是否开放
telnet your-platform.com 8080

# 或使用 nc
nc -zv your-platform.com 8080
```

**解决**：
1. 确认服务已启动
2. 检查防火墙设置
3. 确认网络路由

### 方案 4：认证问题

**问题**：API需要认证但系统未提供

**当前状态**：系统暂不支持API认证

**临时解决**：
- 如果是内网环境，可以配置API不需要认证
- 如果必须认证，需要扩展代码支持认证

**代码扩展示例**：

编辑 `backend/app/services/automation_service.py`：

```python
def __init__(self):
    self.base_url = settings.AUTOMATION_PLATFORM_API_BASE
    # 添加认证支持
    self.api_key = settings.AUTOMATION_PLATFORM_API_KEY  # 需要在配置中添加
    self.headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }

def create_case(self, ...):
    # 使用headers
    response = requests.post(url, json=payload, headers=self.headers, timeout=30)
```

### 方案 5：API返回格式不正确

**问题**：API返回的不是标准JSON格式

**检查**：
```bash
curl -X POST http://your-platform.com/usercase/case/addCase \
  -H "Content-Type: application/json" \
  -d '{"name":"test"}' | jq .
```

如果 `jq` 报错，说明返回的不是JSON。

**解决**：
1. 确认API实现是否正确
2. 联系自动化平台开发人员
3. 确认API文档与实际实现是否一致

## 📋 常见错误场景

### 场景 1：404 Not Found

**日志：**
```
[INFO] 响应状态码: 404
[INFO] 响应内容: <!DOCTYPE html>...404 Not Found...
```

**原因：** API路径不存在

**解决：**
- 检查API地址配置
- 确认接口路径是否正确
- 联系自动化平台确认API地址

### 场景 2：500 Internal Server Error

**日志：**
```
[INFO] 响应状态码: 500
[INFO] 响应内容: Internal Server Error
```

**原因：** 自动化平台服务器内部错误

**解决：**
- 检查发送的数据是否正确
- 查看自动化平台的日志
- 确认必填字段是否都提供了

### 场景 3：Connection Refused

**错误：**
```
无法连接到自动化平台: http://...
ConnectionRefusedError: [Errno 111] Connection refused
```

**原因：** 服务未启动或端口不正确

**解决：**
- 确认服务已启动
- 检查端口号是否正确
- 确认防火墙未阻止

### 场景 4：Timeout

**错误：**
```
调用自动化平台超时（30秒）
```

**原因：** 网络慢或服务响应慢

**解决：**
- 检查网络连接
- 确认服务是否正常运行
- 可以增加超时时间（修改代码中的timeout参数）

## 🧪 完整测试流程

### 1. 环境检查

```bash
# 检查配置
cd backend
python -c "from app.core.config import settings; print('API Base:', settings.AUTOMATION_PLATFORM_API_BASE)"
```

### 2. 运行诊断工具

```bash
python test_automation_connection.py
```

### 3. 手动测试API

```bash
# 测试连接
curl -v http://your-platform.com

# 测试创建接口（替换为实际地址和数据）
curl -X POST http://your-platform.com/usercase/case/addCase \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试",
    "moduleId": "实际模块ID",
    "sceneId": "实际场景ID",
    "scenarioType": "API"
  }'
```

### 4. 查看系统日志

```bash
# 重启后端（启用详细日志）
cd backend
python main.py

# 在另一个终端查看日志
tail -f logs/app.log
```

### 5. 在前端测试

1. 进入测试用例页面
2. 点击"自动化"按钮
3. 输入有效的模块ID
4. 查看错误信息和后端日志

## 📞 获取帮助

如果以上方法都无法解决问题，请收集以下信息：

1. **诊断工具输出**
   ```bash
   python test_automation_connection.py > diagnosis.log 2>&1
   ```

2. **后端日志**
   ```bash
   tail -100 logs/app.log > backend.log
   ```

3. **配置信息**
   ```bash
   # 隐藏敏感信息后
   cat backend/.env | grep AUTOMATION_PLATFORM
   ```

4. **手动curl测试结果**
   ```bash
   curl -v http://your-platform.com 2>&1 | head -50
   ```

5. **系统环境**
   - 操作系统
   - Python版本
   - 是否使用Docker
   - 网络环境（内网/外网/VPN等）

将这些信息提供给技术支持团队。

## 🔗 相关文档

- [快速开始指南](./AUTOMATION_QUICK_START.md)
- [集成说明文档](./AUTOMATION_PLATFORM_INTEGRATION.md)
- [配置更新说明](./AUTOMATION_CONFIG_UPDATE.md)
- [环境配置说明](./backend/ENVIRONMENT_SETUP.md)

---

**最后更新**: 2024-12-16  
**版本**: v1.2.1

