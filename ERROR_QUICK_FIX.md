# ❌ 错误快速修复：Expecting value: line 1 column 1

## 🎯 快速诊断（3分钟）

遇到 **"Expecting value: line 1 column 1 (char 0)"** 错误？这是API返回非JSON格式的问题。

### 立即运行诊断工具

```bash
cd backend
python test_automation_connection.py
```

这个工具会自动检测问题并给出建议。

## 🔍 最常见的3个原因

### 1️⃣ API地址配置错误（90%的情况）

**检查：** 系统配置 → 第三方接入 → API地址

**常见错误：**
```
❌ 192.168.1.100:8080           (缺少 http://)
❌ http://192.168.1.100:8080/   (末尾不要斜杠)
❌ http://192.168.1.100:8080/api (不要包含路径)
```

**正确格式：**
```
✅ http://192.168.1.100:8080
✅ https://autotest.example.com
```

**快速测试：**
```bash
# 替换为你的地址
curl http://your-platform.com
```

如果返回404或HTML错误页，说明地址不对。

### 2️⃣ 自动化平台服务未启动

**检查：**
```bash
# 能ping通吗？
ping your-platform.com

# 端口开放吗？
telnet your-platform.com 8080
# 或
nc -zv your-platform.com 8080
```

**解决：**
- 启动自动化测试平台服务
- 检查防火墙设置

### 3️⃣ API路径不匹配

**系统调用的接口：**
```
POST /usercase/case/addCase
GET  /api/automation/bom/variable/{sceneId}/{usercaseId}
```

**测试接口是否存在：**
```bash
curl -X POST http://your-platform.com/usercase/case/addCase \
  -H "Content-Type: application/json" \
  -d '{"name":"test","moduleId":"test","sceneId":"test","scenarioType":"API"}'
```

**期望返回JSON：**
```json
{
  "success": true,
  "data": {...}
}
```

**如果返回HTML或404：**
- API路径不对
- 需要确认正确的接口地址

## ⚡ 5步快速修复

### Step 1: 确认API地址

```bash
# 在浏览器或curl访问基础地址
curl http://your-platform.com
```

应该能访问，不报错。

### Step 2: 测试完整接口

```bash
curl -X POST http://your-platform.com/usercase/case/addCase \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试",
    "moduleId": "你的模块ID",
    "sceneId": "测试场景ID",
    "scenarioType": "API"
  }'
```

应该返回JSON格式的响应。

### Step 3: 更新系统配置

1. 登录系统（管理员）
2. 系统配置 → 第三方接入
3. 更新API地址为正确的地址
4. 保存

### Step 4: 查看详细日志

现在后端会输出详细日志：

```bash
# 启动后端
cd backend
python main.py

# 查看日志
tail -f logs/app.log | grep "调用自动化平台"
```

### Step 5: 重新测试

在前端点击"自动化"按钮，查看是否成功。

## 📝 查看详细日志

后端现在会输出详细的调试信息：

```
[INFO] 调用自动化平台创建用例
[INFO] URL: http://192.168.1.100:8080/usercase/case/addCase
[INFO] Payload: {'name': '测试用例', ...}
[INFO] 响应状态码: 404
[INFO] 响应内容: <!DOCTYPE html>...
```

从这些信息可以看出具体问题。

## 🆘 仍然无法解决？

### 运行完整诊断

```bash
cd backend
python test_automation_connection.py > diagnosis.txt 2>&1
```

查看 `diagnosis.txt` 文件，会有详细的诊断信息。

### 收集信息

1. 诊断工具输出
2. 后端日志（最后100行）
3. 手动curl测试结果
4. 系统配置截图

### 查看完整文档

详细的排查步骤和解决方案：
📖 [故障排除指南](./AUTOMATION_TROUBLESHOOTING.md)

### 联系支持

提供上述收集的信息给技术支持。

---

**提示：** 95%的情况下，问题都是API地址配置不正确导致的。请仔细检查地址格式！

