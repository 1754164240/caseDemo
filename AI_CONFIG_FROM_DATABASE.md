# AI配置从数据库读取 - 修复说明

## 问题描述

用户在系统配置中设置了以下配置：
- AI模型配置中的 temperature = 1.0
- 自动化测试平台的 API 地址

但是系统运行时：
1. **温度参数问题**：AI服务初始化时显示温度为 0.7，而不是数据库中配置的 1.0
2. **自动化服务不可用**：提示"自动化测试平台服务未配置或不可用"

## 根本原因

### 问题1：温度参数硬编码

在 `backend/app/services/ai_service.py` 中，当无法从数据库读取配置时，回退到环境变量配置使用了硬编码的温度值：

```python
# 回退到环境变量配置
return {
    "api_key": settings.OPENAI_API_KEY,
    "api_base": settings.OPENAI_API_BASE,
    "model_name": settings.MODEL_NAME,
    "temperature": "0.7",  # ❌ 硬编码
    "max_tokens": None,
    "provider": None,
}
```

### 问题2：缺少数据库连接

多个地方在调用 AI 和自动化服务时，没有传入数据库连接（`db`），导致服务无法从数据库读取配置：

1. `test_cases.py` 第706行：`ai_service_instance = get_ai_service()` ❌
2. `test_cases.py` 第628行：虽然创建了新的 automation_service，但 `get_automation_service()` 函数本身只检查环境变量
3. `automation_service.py` 第210行：`ai_service = get_ai_service()` ❌

### 问题3：自动化服务只检查环境变量

`get_automation_service()` 函数只检查 `settings.AUTOMATION_PLATFORM_API_BASE`，不从数据库读取：

```python
if not settings.AUTOMATION_PLATFORM_API_BASE:  # ❌ 只检查环境变量
    print("[WARNING] 自动化平台 API 地址未配置")
    return None
```

## 解决方案

### 1. 修复温度参数硬编码

**文件**：`backend/app/core/config.py`

添加 AI_TEMPERATURE 配置项：

```python
# LLM retry
AI_MAX_RETRIES: int = 3
AI_RETRY_INTERVAL: float = 2.0
AI_REQUEST_TIMEOUT: int = 180
AI_TEMPERATURE: float = 1.0  # ✅ AI 温度参数默认值
```

**文件**：`backend/app/services/ai_service.py`

修改回退配置读取：

```python
# 回退到环境变量配置
# 从settings读取temperature配置，如果没有则使用1.0
default_temp = getattr(settings, 'AI_TEMPERATURE', 1.0)  # ✅
return {
    "api_key": settings.OPENAI_API_KEY,
    "api_base": settings.OPENAI_API_BASE,
    "model_name": settings.MODEL_NAME,
    "temperature": str(default_temp),  # ✅
    "max_tokens": None,
    "provider": None,
}
```

### 2. 传入数据库连接

**文件**：`backend/app/api/v1/endpoints/test_cases.py`

```python
# ✅ 生成测试用例时
ai_svc = get_ai_service(db)  # 已经正确

# ✅ 匹配场景时
ai_service_instance = get_ai_service(db)  # 添加 db 参数

# ✅ 获取自动化服务时
automation_service = get_automation_service(db)  # 添加 db 参数
```

**文件**：`backend/app/services/automation_service.py`

```python
class AutomationPlatformService:
    def __init__(self, base_url: str, db=None):  # ✅ 添加 db 参数
        self.base_url = base_url
        self.db = db  # ✅ 保存数据库连接

def select_best_case_by_ai(...):
    # ✅ 传入db以读取数据库配置
    ai_service = get_ai_service(self.db)
```

### 3. 从数据库读取自动化平台配置

**文件**：`backend/app/services/automation_service.py`

修改 `get_automation_service()` 函数：

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
            
        return AutomationPlatformService(base_url=api_base, db=db)  # ✅ 传入 base_url 和 db
    except Exception as e:
        print(f"[WARNING] 初始化自动化平台服务失败: {e}")
        return None
```

## 修改文件清单

1. ✅ `backend/app/core/config.py` - 添加 `AI_TEMPERATURE` 配置项
2. ✅ `backend/app/services/ai_service.py` - 修复温度参数硬编码
3. ✅ `backend/app/api/v1/endpoints/test_cases.py` - 传入 db 参数
4. ✅ `backend/app/services/automation_service.py` - 从数据库读取配置

## 验证步骤

### 1. 重启后端服务

```bash
cd backend
python main.py
```

### 2. 检查启动日志

应该看到类似的日志：

```
[INFO] 初始化 AI 服务 - 模型: glm-4.6, 超时: 180秒, 温度: 1.0, 最大重试: 3次
```

**注意**：温度现在应该显示为 **1.0**（数据库配置）而不是 0.7

### 3. 测试自动化用例生成

1. 在测试用例页面点击"自动化"按钮
2. 检查后端日志，应该看到：

```
[INFO] 从数据库读取自动化平台API地址: http://localhost:8087
[INFO] 调用自动化平台创建用例和明细
```

**注意**：应该能成功读取数据库中配置的API地址

## 配置优先级

现在系统采用以下配置优先级：

### AI 服务配置
1. 数据库中的模型配置（`model_config` 表）
2. `backend/app/core/config.py` 中的 `AI_TEMPERATURE`
3. 环境变量（`.env` 文件）

### 自动化平台配置
1. 数据库中的系统配置（`system_config` 表，通过系统设置页面管理）
2. 环境变量（`settings.AUTOMATION_PLATFORM_API_BASE`）

## 优势

1. **配置灵活**：优先使用数据库配置，允许运行时动态修改
2. **向后兼容**：保留环境变量作为回退，兼容旧的部署方式
3. **日志清晰**：明确记录配置来源（数据库 vs 环境变量）
4. **用户友好**：用户可以通过UI修改配置，无需重启服务

## 相关文档

- [系统配置管理](./AUTOMATION_CONFIG_UPDATE.md)
- [AI服务配置](./backend/ENVIRONMENT_SETUP.md)
- [自动化平台集成](./AUTOMATION_PLATFORM_INTEGRATION.md)


