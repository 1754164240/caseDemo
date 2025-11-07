# Python 3.13 兼容性说明

## 问题描述

在 Python 3.13 环境下安装依赖时，`psycopg2-binary` 会出现编译错误：

```
error: Microsoft Visual C++ 14.0 or greater is required.
```

这是因为 `psycopg2-binary` 目前还没有为 Python 3.13 提供预编译的二进制包。

## 解决方案

我们已对项目进行了以下升级以支持 Python 3.13：

1. **PostgreSQL 驱动**: `psycopg2-binary` → `psycopg` v3
2. **SQLAlchemy**: 升级到 2.0.36+ (支持 Python 3.13)
3. **配置格式**: 优化环境变量配置

### 主要变更

#### 1. 依赖包变更

**PostgreSQL 驱动**:
- 之前: `psycopg2-binary==2.9.9`
- 现在: `psycopg[binary]==3.2.3`

**SQLAlchemy**:
- 之前: `sqlalchemy==2.0.25` (不支持 Python 3.13)
- 现在: `sqlalchemy==2.0.36` (完全支持 Python 3.13)

**配置管理**:
- 之前: `pydantic-settings==2.1.0`
- 现在: `pydantic-settings==2.11.0` (使用新的 API)

#### 2. 数据库 URL 格式变更

**之前**:
```env
DATABASE_URL=postgresql://testcase:testcase123@localhost:5432/test_case_db
```

**现在**:
```env
DATABASE_URL=postgresql+psycopg://testcase:testcase123@localhost:5432/test_case_db
```

注意：添加了 `+psycopg` 来明确指定使用 psycopg 驱动。

#### 3. CORS 配置格式变更

**之前** (不兼容 pydantic-settings 2.11+):
```env
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
```

**现在** (逗号分隔字符串):
```env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

注意：新版本 pydantic-settings 对 JSON 格式的环境变量解析更严格，使用逗号分隔更简单可靠。

### psycopg vs psycopg2

`psycopg` (版本 3) 是 `psycopg2` 的下一代版本，具有以下优势：

✅ **原生支持 Python 3.13**  
✅ **更好的性能**  
✅ **异步支持更完善**  
✅ **类型提示更好**  
✅ **API 更现代化**  
✅ **不需要编译器**（使用 binary 版本）

### API 兼容性

好消息是，SQLAlchemy 2.0 完全支持 psycopg 3，并且大部分 API 是兼容的。我们的代码不需要做任何修改，只需要：

1. 更新 `requirements.txt` 中的依赖
2. 更新 `DATABASE_URL` 格式（添加 `+psycopg`）

### 安装步骤

#### 方法 1：使用安装脚本（推荐）

```bash
# Windows
install-backend.bat

# Linux/Mac
pip install -r backend/requirements.txt
```

#### 方法 2：手动安装

```bash
cd backend
pip install -r requirements.txt
```

### 环境配置

#### 创建 .env 文件

**方法 1：使用脚本（推荐）**
```bash
# Windows
setup-env.bat
```

**方法 2：手动创建**
```bash
cd backend
copy .env.example .env
```

#### 配置必要参数

编辑 `backend/.env` 文件：

```env
# 数据库 URL（必须使用 postgresql+psycopg:// 格式）
DATABASE_URL=postgresql+psycopg://testcase:testcase123@localhost:5432/test_case_db

# OpenAI API Key（必须配置）
OPENAI_API_KEY=sk-your-api-key-here

# CORS 配置（逗号分隔，不要使用 JSON 格式）
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

**重要提示**：
- ✅ 正确: `CORS_ORIGINS=http://localhost:5173,http://localhost:3000`
- ❌ 错误: `CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]`

### 验证安装

安装完成后，可以通过以下方式验证：

```python
# 在 Python 中运行
import psycopg
print(psycopg.__version__)  # 应该显示 3.2.3 或更高版本
```

### 其他依赖更新

我们还更新了其他依赖包以确保与 Python 3.13 的兼容性：

```
python-dotenv==1.2.1        # 从 1.0.0 升级
alembic==1.17.1             # 从 1.13.1 升级
pydantic==2.12.4            # 从 2.5.3 升级
pydantic-settings==2.11.0   # 从 2.1.0 升级
langchain==1.0.3            # 从 1.0.2 升级
openai==2.7.1               # 从 1.59.5 升级
pymilvus==2.6.3             # 从 2.3.5 升级
```

### 常见问题

#### Q: 为什么不安装 Visual C++ Build Tools？

A: 虽然安装 Build Tools 可以编译 `psycopg2-binary`，但：
- 下载和安装需要几个 GB 的空间
- 安装过程较长
- `psycopg` 是更现代的解决方案
- `psycopg[binary]` 提供预编译版本，无需编译器

#### Q: psycopg 和 psycopg2 有什么区别？

A: 主要区别：
- `psycopg` (v3) 是全新设计的版本
- 更好的异步支持
- 更好的类型提示
- 更现代的 API
- 但基本用法与 psycopg2 兼容

#### Q: 需要修改代码吗？

A: 不需要！SQLAlchemy 会自动处理驱动差异。只需要：
1. 更新 requirements.txt
2. 更新 DATABASE_URL 格式

#### Q: 如果我想继续使用 psycopg2 怎么办？

A: 您需要：
1. 安装 [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. 或者降级到 Python 3.12 或更早版本

但我们强烈推荐使用 `psycopg`，因为它是未来的方向。

### 迁移检查清单

- [x] 更新 `backend/requirements.txt`
- [x] 更新 `backend/.env.example`
- [x] 更新 `backend/app/core/config.py` 默认值
- [x] 测试数据库连接
- [x] 测试所有 API 端点
- [x] 更新文档

### 参考资料

- [psycopg 官方文档](https://www.psycopg.org/psycopg3/)
- [SQLAlchemy psycopg 支持](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg)
- [从 psycopg2 迁移到 psycopg](https://www.psycopg.org/psycopg3/docs/basic/from_pg2.html)

## 总结

通过升级到 `psycopg`，我们不仅解决了 Python 3.13 的兼容性问题，还获得了更好的性能和更现代的 API。这是一个向前兼容的升级，不会影响现有功能。

