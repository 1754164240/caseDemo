# v1.3.5 配置从数据库读取 - 更新说明

**版本**：v1.3.5  
**发布日期**：2024-12-18  
**更新类型**：🔧 Bug修复 + ⚙️ 配置优化

---

## 🎯 更新概述

本次更新修复了两个配置相关的关键问题：
1. **AI温度参数问题**：数据库配置的temperature=1.0被硬编码的0.7覆盖
2. **自动化服务不可用**：服务只检查环境变量，无法读取数据库中的API地址配置

---

## 🐛 修复的问题

### 问题1：温度参数被硬编码覆盖

**症状**：
```bash
[INFO] 初始化 AI 服务 - 模型: glm-4.6, 超时: 180秒, 温度: 0.7, 最大重试: 3次
```

**预期**：应该显示数据库中配置的 `1.0`

**原因**：
- `ai_service.py` 中回退配置使用了硬编码：`"temperature": "0.7"`
- 调用 `get_ai_service()` 时没有传入数据库连接

### 问题2：自动化服务提示未配置

**症状**：
```
自动化测试平台服务未配置或不可用
```

**预期**：应该能读取数据库中配置的API地址

**原因**：
- `get_automation_service()` 只检查环境变量
- 不从数据库的 `system_config` 表读取配置

---

## ✨ 主要改进

### 1. AI服务配置优化

#### 新增配置项

**文件**：`backend/app/core/config.py`

```python
# LLM retry
AI_MAX_RETRIES: int = 3
AI_RETRY_INTERVAL: float = 2.0
AI_REQUEST_TIMEOUT: int = 180
AI_TEMPERATURE: float = 1.0  # ✅ 新增：AI温度参数默认值
```

#### 修复回退配置

**文件**：`backend/app/services/ai_service.py`

```python
# 回退到环境变量配置
default_temp = getattr(settings, 'AI_TEMPERATURE', 1.0)  # ✅ 从settings读取
return {
    "api_key": settings.OPENAI_API_KEY,
    "api_base": settings.OPENAI_API_BASE,
    "model_name": settings.MODEL_NAME,
    "temperature": str(default_temp),  # ✅ 使用配置值
    "max_tokens": None,
    "provider": None,
}
```

### 2. 数据库连接传递

#### 测试用例接口

**文件**：`backend/app/api/v1/endpoints/test_cases.py`

```python
# ✅ 匹配场景时传入db
ai_service_instance = get_ai_service(db)

# ✅ 获取自动化服务时传入db
automation_service = get_automation_service(db)
```

#### 自动化服务

**文件**：`backend/app/services/automation_service.py`

```python
class AutomationPlatformService:
    def __init__(self, base_url: str, db=None):  # ✅ 接收base_url和db
        self.base_url = base_url
        self.db = db  # ✅ 保存数据库连接

def select_best_case_by_ai(...):
    # ✅ 传入db以读取数据库配置
    ai_service = get_ai_service(self.db)
```

### 3. 从数据库读取自动化平台配置

#### 配置读取优先级

**文件**：`backend/app/services/automation_service.py`

```python
def get_automation_service(db=None) -> Optional[AutomationPlatformService]:
    """获取自动化平台服务实例"""
    try:
        # ✅ 优先从数据库读取配置
        api_base = None
        if db:
            try:
                from app.models.system_config import SystemConfig
                config = db.query(SystemConfig).filter(
                    SystemConfig.config_key == "AUTOMATION_PLATFORM_API_BASE"
                ).first()
                if config and config.config_value:
                    api_base = config.config_value
                    print(f"[INFO] 从数据库读取自动化平台API地址: {api_base}")
            except Exception as e:
                print(f"[WARNING] 从数据库读取自动化平台配置失败: {e}")
        
        # ✅ 回退到环境变量
        if not api_base:
            api_base = settings.AUTOMATION_PLATFORM_API_BASE
            if api_base:
                print(f"[INFO] 从环境变量读取自动化平台API地址: {api_base}")
        
        if not api_base:
            print("[WARNING] 自动化平台 API 地址未配置（数据库和环境变量都未找到）")
            return None
            
        return AutomationPlatformService(base_url=api_base, db=db)
    except Exception as e:
        print(f"[WARNING] 初始化自动化平台服务失败: {e}")
        return None
```

---

## 📋 修改文件清单

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `backend/app/core/config.py` | 新增配置 | 添加 `AI_TEMPERATURE` 配置项 |
| `backend/app/services/ai_service.py` | Bug修复 | 修复温度参数硬编码 |
| `backend/app/api/v1/endpoints/test_cases.py` | 优化 | 传入db参数 |
| `backend/app/services/automation_service.py` | 功能增强 | 从数据库读取配置 |

---

## 🔄 配置优先级

### AI 服务配置
```
1. 数据库模型配置 (model_config表)
   ↓ 如果未找到
2. config.py中的AI_TEMPERATURE
   ↓ 如果未设置
3. 默认值 1.0
```

### 自动化平台配置
```
1. 数据库系统配置 (system_config表)
   ↓ 如果未找到
2. 环境变量 (settings.AUTOMATION_PLATFORM_API_BASE)
   ↓ 如果未设置
3. 返回None，提示未配置
```

---

## 🚀 升级步骤

### 1. 更新代码

```bash
# 拉取最新代码
git pull origin main
```

### 2. 重启后端服务

```bash
cd backend
python main.py
```

### 3. 验证日志

启动后应该看到：

```bash
[INFO] 初始化 AI 服务 - 模型: glm-4.6, 超时: 180秒, 温度: 1.0, 最大重试: 3次
```

**注意**：温度现在应该显示为 **1.0** ✅

### 4. 测试自动化功能

1. 在测试用例页面点击"自动化"按钮
2. 查看后端日志：

```bash
[INFO] 从数据库读取自动化平台API地址: http://localhost:8087
[INFO] 调用自动化平台创建用例和明细
```

**注意**：应该能成功读取数据库中的API地址 ✅

---

## 📊 效果对比

### 修复前

| 配置项 | 数据库配置 | 实际使用 | 状态 |
|--------|-----------|---------|------|
| AI温度 | 1.0 | 0.7 | ❌ 被硬编码覆盖 |
| 自动化API | http://localhost:8087 | (空) | ❌ 无法读取 |

### 修复后

| 配置项 | 数据库配置 | 实际使用 | 状态 |
|--------|-----------|---------|------|
| AI温度 | 1.0 | 1.0 | ✅ 正确读取 |
| 自动化API | http://localhost:8087 | http://localhost:8087 | ✅ 正确读取 |

---

## 🎯 用户体验改善

### 修复前
```
❌ 数据库配置不生效
❌ 需要修改代码或环境变量
❌ 自动化服务无法使用
❌ 日志显示错误的配置值
```

### 修复后
```
✅ 数据库配置优先生效
✅ 通过UI即可修改配置
✅ 自动化服务正常工作
✅ 日志显示正确的配置值和来源
```

---

## 🔍 日志增强

新增配置来源日志：

```bash
# AI服务
[INFO] 初始化 AI 服务 - 模型: glm-4.6, 超时: 180秒, 温度: 1.0, 最大重试: 3次

# 自动化服务
[INFO] 从数据库读取自动化平台API地址: http://localhost:8087
# 或
[INFO] 从环境变量读取自动化平台API地址: http://localhost:8087
```

这样可以清楚地知道配置的来源，方便排查问题。

---

## 📝 最佳实践

### 1. 推荐使用数据库配置

- ✅ 可通过UI动态修改
- ✅ 无需重启服务
- ✅ 配置集中管理
- ✅ 支持多环境

### 2. 环境变量作为回退

- 📌 适用于初始部署
- 📌 作为默认值
- 📌 用于快速切换环境

### 3. 配置验证

启动后检查日志，确保：
- 温度参数符合预期
- 自动化API地址正确
- 配置来源清晰

---

## ⚠️ 注意事项

1. **数据库配置优先**：如果数据库和环境变量都有配置，将使用数据库中的值
2. **日志监控**：启动时检查日志，确认配置来源和值
3. **温度范围**：AI temperature 建议设置在 0.0-2.0 之间
4. **API地址格式**：确保自动化平台API地址不包含末尾斜杠

---

## 🔗 相关文档

- [AI配置从数据库读取详细说明](./AI_CONFIG_FROM_DATABASE.md)
- [系统配置管理](./AUTOMATION_CONFIG_UPDATE.md)
- [环境配置说明](./backend/ENVIRONMENT_SETUP.md)
- [快速开始指南](./AUTOMATION_QUICK_START.md)

---

## 📞 技术支持

如有问题或建议，请：
1. 查看详细文档：[AI_CONFIG_FROM_DATABASE.md](./AI_CONFIG_FROM_DATABASE.md)
2. 检查启动日志
3. 联系技术支持团队

---

**版本**：v1.3.5  
**发布日期**：2024-12-18  
**下一版本预告**：更多AI功能优化

