# 快速实施指南：多模型配置功能

## 一、数据库迁移（必须先执行）

```bash
cd backend
python scripts/migrate_model_name_to_array.py
```

**预期输出**：
```
开始迁移 model_name 字段...
1. 修改字段类型为TEXT...
   ✓ 字段类型已修改
2. 查询现有模型配置...
   找到 3 个配置
3. 转换model_name为JSON数组格式...
   - ID 1: 'gpt-4' -> ["gpt-4"]
   - ID 2: 'glm-4.7' -> ["glm-4.7"]
   - ID 3: 'gpt-3.5-turbo' -> ["gpt-3.5-turbo"]
✓ 成功迁移 3 个配置
4. 更新字段注释...
   ✓ 字段注释已更新

✅ 迁移完成!
```

## 二、重启后端服务

```bash
# Windows
cd D:\caseDemo1
bat\start-backend.bat

# 或直接运行
cd backend
python -m scripts.main
```

## 三、测试功能

### 1. 访问模型配置页面

打开浏览器：`http://localhost:5173/model-configs`

### 2. 查看现有配置

- 所有模型名称应显示为标签形式
- 每个模型一个蓝色标签

### 3. 创建多模型配置

点击"添加模型配置"，填写：

```
配置名称: test-multi-model
显示名称: 测试多模型配置
API Key: sk-test-key
API Base URL: https://api.openai.com/v1
模型名称: 选择 gpt-4, gpt-3.5-turbo, glm-4 (多选)
温度参数: 0.7
提供商: openai
启用: ✓
```

点击保存后，表格中应显示：
```
[gpt-4] [gpt-3.5-turbo] [glm-4]
```

### 4. 编辑现有配置

- 点击编辑按钮
- 在模型名称字段添加更多模型
- 或删除某些模型
- 保存并验证

## 四、验证API响应

### 查询配置列表

```bash
curl -H "Authorization: Bearer <your_token>" \
  http://localhost:8000/api/v1/model-configs/
```

**预期响应**：
```json
[
  {
    "id": 1,
    "name": "test-multi-model",
    "model_name": ["gpt-4", "gpt-3.5-turbo", "glm-4"],
    ...
  }
]
```

### 创建新配置

```bash
curl -X POST \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "api-test",
    "display_name": "API测试",
    "api_key": "sk-xxx",
    "api_base": "https://api.test.com",
    "model_name": ["model-1", "model-2"]
  }' \
  http://localhost:8000/api/v1/model-configs/
```

## 五、常见问题排查

### 问题1：迁移脚本报错

**错误**: `ModuleNotFoundError: No module named 'app'`

**解决**:
```bash
cd backend
python -m scripts.migrate_model_name_to_array
```

### 问题2：前端显示不正常

**症状**: 模型名称显示为字符串而不是标签

**解决**:
1. 清除浏览器缓存
2. 强制刷新 (Ctrl+Shift+R)
3. 检查后端日志确认迁移成功

### 问题3：创建配置时验证失败

**错误**: `model_name必须是字符串或字符串数组`

**解决**:
- 确保选择了至少一个模型
- 检查前端是否正确发送数组格式

### 问题4：旧配置显示异常

**症状**: 旧配置的模型名称显示为 `["gpt-4"]` 字符串

**原因**: 迁移脚本未正确执行

**解决**:
```bash
# 重新运行迁移脚本
cd backend
python scripts/migrate_model_name_to_array.py
```

## 六、回滚方案（如有问题）

### 1. 恢复数据库（如有备份）

```sql
-- 恢复到迁移前的状态
\i backup/model_configs_before_migration.sql
```

### 2. 手动修复单个配置

```sql
-- 将JSON数组改回单个字符串
UPDATE model_configs
SET model_name = 'gpt-4'
WHERE id = 1;
```

### 3. 恢复代码（如有Git）

```bash
git checkout HEAD -- backend/app/models/model_config.py
git checkout HEAD -- backend/app/schemas/model_config.py
git checkout HEAD -- backend/app/api/v1/endpoints/model_config.py
git checkout HEAD -- frontend/src/pages/ModelConfigs.tsx
```

## 七、验收标准

- [ ] 迁移脚本执行成功，无错误
- [ ] 后端服务启动正常
- [ ] 前端页面加载正常
- [ ] 现有配置显示为标签数组
- [ ] 可以创建多模型配置
- [ ] 可以编辑并更新模型列表
- [ ] API响应包含model_name数组
- [ ] 表格正确显示多个模型标签

## 八、下一步

实施完成后，可以：

1. **更新AI服务调用逻辑**
   - 实现模型降级机制
   - 添加失败重试逻辑

2. **监控和日志**
   - 记录每个模型的使用次数
   - 监控模型调用成功率

3. **用户培训**
   - 编写用户手册
   - 演示多模型配置的好处

---

**预计耗时**: 15分钟
**风险等级**: 低（向后兼容）
**紧急程度**: 中等
