"""
配置检查脚本 - 用于诊断配置问题
"""
import os
import sys

print("=" * 60)
print("配置检查脚本")
print("=" * 60)
print()

# 检查 .env 文件
env_file = ".env"
if os.path.exists(env_file):
    print(f"✅ {env_file} 文件存在")
    print()
    print("环境变量内容:")
    print("-" * 60)
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # 隐藏敏感信息
                if 'API_KEY' in line or 'SECRET' in line or 'PASSWORD' in line:
                    key = line.split('=')[0]
                    print(f"{key}=***隐藏***")
                else:
                    print(line)
    print("-" * 60)
else:
    print(f"❌ {env_file} 文件不存在")
    print()
    print("请运行以下命令创建配置文件:")
    print("  copy .env.example .env")
    print()
    sys.exit(1)

print()

# 尝试加载配置
try:
    from app.core.config import settings
    print("✅ 配置加载成功")
    print()
    print("当前配置:")
    print("-" * 60)
    print(f"DATABASE_URL: {settings.DATABASE_URL[:30]}...")
    print(f"MILVUS_HOST: {settings.MILVUS_HOST}")
    print(f"MILVUS_PORT: {settings.MILVUS_PORT}")
    print(f"MODEL_NAME: {settings.MODEL_NAME}")
    print(f"OPENAI_API_KEY: {'已配置' if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != '' else '未配置'}")
    print(f"CORS_ORIGINS: {settings.CORS_ORIGINS}")
    print("-" * 60)
    print()
    
    # 检查 DATABASE_URL 格式
    if settings.DATABASE_URL.startswith("postgresql+psycopg://"):
        print("✅ DATABASE_URL 格式正确 (使用 psycopg 驱动)")
    elif settings.DATABASE_URL.startswith("postgresql://"):
        print("❌ DATABASE_URL 格式错误")
        print()
        print("当前格式: postgresql://...")
        print("正确格式: postgresql+psycopg://...")
        print()
        print("请修改 .env 文件中的 DATABASE_URL:")
        print("  DATABASE_URL=postgresql+psycopg://testcase:testcase123@localhost:5432/test_case_db")
        print()
        sys.exit(1)
    else:
        print(f"⚠️  DATABASE_URL 格式未知: {settings.DATABASE_URL[:20]}...")
    
    print()
    
    # 检查 OPENAI_API_KEY
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "":
        print("⚠️  OPENAI_API_KEY 未配置")
        print("   AI 功能将无法使用")
    elif settings.OPENAI_API_KEY.startswith("sk-"):
        print("✅ OPENAI_API_KEY 已配置")
    else:
        print("⚠️  OPENAI_API_KEY 格式可能不正确")
        print("   OpenAI API Key 通常以 'sk-' 开头")
    
    print()
    
except Exception as e:
    print(f"❌ 配置加载失败: {e}")
    print()
    import traceback
    traceback.print_exc()
    print()
    sys.exit(1)

# 检查数据库连接
print("检查数据库连接...")
print("-" * 60)
try:
    from sqlalchemy import create_engine, text
    
    # 尝试创建引擎
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    print(f"✅ 数据库引擎创建成功")
    print(f"   驱动: {engine.dialect.name}")
    print(f"   DBAPI: {engine.dialect.dbapi.__name__ if hasattr(engine.dialect, 'dbapi') else 'N/A'}")
    
    # 尝试连接
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ 数据库连接成功")
            print(f"   PostgreSQL 版本: {version.split(',')[0]}")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print()
        print("可能的原因:")
        print("1. Docker 容器未启动 - 运行: docker-compose up -d")
        print("2. 数据库凭据错误 - 检查 .env 文件")
        print("3. 端口被占用 - 检查端口 5432")
        
except ModuleNotFoundError as e:
    print(f"❌ 缺少模块: {e}")
    print()
    if "psycopg2" in str(e):
        print("错误: 尝试导入 psycopg2 但未安装")
        print()
        print("解决方案:")
        print("1. 检查 DATABASE_URL 是否使用 'postgresql+psycopg://' 格式")
        print("2. 确保安装了 psycopg (不是 psycopg2):")
        print("   pip install 'psycopg[binary]==3.2.3'")
        print()
    elif "psycopg" in str(e):
        print("错误: psycopg 未安装")
        print()
        print("解决方案:")
        print("   pip install 'psycopg[binary]==3.2.3'")
        print()
except Exception as e:
    print(f"❌ 数据库检查失败: {e}")
    import traceback
    traceback.print_exc()

print("-" * 60)
print()

# 检查已安装的包
print("检查关键依赖包...")
print("-" * 60)
try:
    import sqlalchemy
    print(f"✅ sqlalchemy: {sqlalchemy.__version__}")
except ImportError:
    print("❌ sqlalchemy 未安装")

try:
    import psycopg
    print(f"✅ psycopg: {psycopg.__version__}")
except ImportError:
    print("❌ psycopg 未安装 - 请运行: pip install 'psycopg[binary]==3.2.3'")

try:
    import psycopg2
    print(f"⚠️  psycopg2: {psycopg2.__version__} (不应该安装)")
except ImportError:
    print("✅ psycopg2 未安装 (正确)")

try:
    import fastapi
    print(f"✅ fastapi: {fastapi.__version__}")
except ImportError:
    print("❌ fastapi 未安装")

try:
    import pydantic
    print(f"✅ pydantic: {pydantic.__version__}")
except ImportError:
    print("❌ pydantic 未安装")

try:
    import email_validator
    print(f"✅ email-validator: {email_validator.__version__}")
except ImportError:
    print("❌ email-validator 未安装 - 请运行: pip install email-validator==2.1.0")

print("-" * 60)
print()

print("=" * 60)
print("检查完成！")
print("=" * 60)

