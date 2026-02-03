"""
添加 selected_model 字段的数据库迁移脚本
"""
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from app.core.config import settings


def migrate_add_selected_model():
    """添加 selected_model 字段并设置默认值"""

    print("开始添加 selected_model 字段...")

    engine = create_engine(str(settings.DATABASE_URL))

    with engine.connect() as conn:
        # 1. 添加 selected_model 字段
        print("1. 添加 selected_model 字段...")
        try:
            conn.execute(text(
                "ALTER TABLE model_configs ADD COLUMN IF NOT EXISTS selected_model VARCHAR(200)"
            ))
            conn.commit()
            print("   ✓ 字段已添加")
        except Exception as e:
            print(f"   注意: {e}")
            conn.rollback()

        # 2. 为现有数据设置默认值（选择第一个模型）
        print("2. 为现有数据设置默认值...")
        result = conn.execute(text("SELECT id, model_name FROM model_configs WHERE selected_model IS NULL"))
        configs = result.fetchall()

        updated_count = 0
        for config_id, model_name in configs:
            try:
                # 解析JSON数组
                models = json.loads(model_name)
                if isinstance(models, list) and len(models) > 0:
                    first_model = models[0]
                else:
                    first_model = model_name

                # 设置第一个模型为默认选中
                conn.execute(
                    text("UPDATE model_configs SET selected_model = :model WHERE id = :id"),
                    {"model": first_model, "id": config_id}
                )
                updated_count += 1
                print(f"   - ID {config_id}: 设置 selected_model = '{first_model}'")
            except (json.JSONDecodeError, ValueError):
                # 如果不是JSON，直接使用原值
                conn.execute(
                    text("UPDATE model_configs SET selected_model = :model WHERE id = :id"),
                    {"model": model_name, "id": config_id}
                )
                updated_count += 1
                print(f"   - ID {config_id}: 设置 selected_model = '{model_name}'")

        conn.commit()
        print(f"   ✓ 已更新 {updated_count} 个配置")

        # 3. 更新字段注释
        print("3. 更新字段注释...")
        try:
            conn.execute(text(
                "COMMENT ON COLUMN model_configs.selected_model IS '当前选中使用的模型名称'"
            ))
            conn.commit()
            print("   ✓ 字段注释已更新")
        except Exception as e:
            print(f"   注意: {e}")

        print("\n✅ 迁移完成!")
        print("\n建议：")
        print("1. 重启后端服务")
        print("2. 刷新前端页面")
        print("3. 测试创建/编辑模型配置功能")


if __name__ == "__main__":
    try:
        migrate_add_selected_model()
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
