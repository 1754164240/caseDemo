"""
测试并修复Dashboard模型显示问题
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.model_config import ModelConfig
from app.models.user import User
import json

def test_dashboard_model_display():
    """测试Dashboard模型显示"""

    engine = create_engine(str(settings.DATABASE_URL))
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 获取默认模型配置
        config = db.query(ModelConfig).filter(
            ModelConfig.is_default == True,
            ModelConfig.is_active == True
        ).first()

        if not config:
            print("❌ 未找到默认模型配置")
            return

        print("=" * 60)
        print("数据库原始数据:")
        print("=" * 60)
        print(f"配置名称: {config.display_name}")
        print(f"model_name (原始): {repr(config.model_name)}")
        print(f"selected_model: {repr(config.selected_model)}")
        print()

        # 解析 model_name
        model_names = config.model_name
        if isinstance(model_names, str):
            try:
                parsed = json.loads(model_names)
                print(f"model_name (解析后): {parsed}")
                print(f"类型: {type(parsed)}")
                model_names = parsed
            except Exception as e:
                print(f"❌ JSON解析失败: {e}")
                model_names = [model_names]

        # 当前使用的模型
        current_model = config.selected_model or (model_names[0] if model_names else "N/A")

        print()
        print("=" * 60)
        print("API应该返回的数据:")
        print("=" * 60)

        model_config_info = {
            "config_name": config.display_name,
            "current_model": current_model,
            "all_models": model_names if isinstance(model_names, list) else [model_names],
            "provider": config.provider,
            "api_base": config.api_base
        }

        print(json.dumps(model_config_info, indent=2, ensure_ascii=False))

        print()
        print("=" * 60)
        print("前端应该显示:")
        print("=" * 60)
        print(f"当前模型: {current_model}")
        print(f"配置名称: {config.display_name}")
        print(f"所有模型: {model_names}")
        print(f"提供商: {config.provider}")

        # 验证数据类型
        print()
        print("=" * 60)
        print("数据类型验证:")
        print("=" * 60)
        print(f"all_models 是列表: {isinstance(model_config_info['all_models'], list)}")
        print(f"current_model 是字符串: {isinstance(model_config_info['current_model'], str)}")

        if isinstance(model_config_info['all_models'], list):
            print(f"✅ all_models 是正确的列表类型")
            for idx, model in enumerate(model_config_info['all_models']):
                print(f"  [{idx}] {model} ({type(model).__name__})")
        else:
            print(f"❌ all_models 类型错误: {type(model_config_info['all_models'])}")

    finally:
        db.close()


if __name__ == "__main__":
    test_dashboard_model_display()
