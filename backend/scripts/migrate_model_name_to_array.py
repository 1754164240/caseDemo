"""
数据库迁移脚本：model_name字段支持多模型配置

将现有的单个模型名称转换为JSON数组格式
"""
import sys
import os
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from app.core.config import settings


def migrate_model_names():
    """将model_name从单个字符串迁移到JSON数组格式"""

    print("开始迁移 model_name 字段...")

    # 创建数据库连接
    engine = create_engine(str(settings.DATABASE_URL))

    with engine.connect() as conn:
        # 1. 修改字段类型为TEXT
        print("1. 修改字段类型为TEXT...")
        try:
            conn.execute(text("ALTER TABLE model_configs ALTER COLUMN model_name TYPE TEXT"))
            conn.commit()
            print("   ✓ 字段类型已修改")
        except Exception as e:
            print(f"   注意: {e}")
            print("   (如果字段已经是TEXT类型，可以忽略此错误)")

        # 2. 查询所有现有配置
        print("2. 查询现有模型配置...")
        result = conn.execute(text("SELECT id, model_name FROM model_configs"))
        configs = result.fetchall()
        print(f"   找到 {len(configs)} 个配置")

        # 3. 转换数据
        print("3. 转换model_name为JSON数组格式...")
        migrated_count = 0

        for config_id, model_name in configs:
            # 跳过已经是JSON数组格式的
            if model_name and model_name.startswith('['):
                print(f"   - ID {config_id}: 已经是JSON数组格式，跳过")
                continue

            # 转换为JSON数组
            if model_name:
                new_model_name = json.dumps([model_name], ensure_ascii=False)
            else:
                new_model_name = json.dumps([], ensure_ascii=False)

            # 更新数据库
            conn.execute(
                text("UPDATE model_configs SET model_name = :new_name WHERE id = :id"),
                {"new_name": new_model_name, "id": config_id}
            )
            migrated_count += 1
            print(f"   - ID {config_id}: '{model_name}' -> {new_model_name}")

        conn.commit()
        print(f"✓ 成功迁移 {migrated_count} 个配置")

        # 4. 更新字段注释
        print("4. 更新字段注释...")
        try:
            conn.execute(text(
                "COMMENT ON COLUMN model_configs.model_name IS "
                "'模型名称列表(JSON数组格式,如[\"gpt-4\",\"gpt-3.5-turbo\"])'"
            ))
            conn.commit()
            print("   ✓ 字段注释已更新")
        except Exception as e:
            print(f"   注意: {e}")

        print("\n✅ 迁移完成!")
        print("\n建议：")
        print("1. 重启后端服务以应用更改")
        print("2. 在模型配置页面验证数据显示正确")
        print("3. 尝试创建/更新模型配置，测试多模型功能")


if __name__ == "__main__":
    try:
        migrate_model_names()
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
