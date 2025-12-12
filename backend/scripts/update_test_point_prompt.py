"""更新测试点生成 Prompt 配置，添加业务线识别。"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings


def update_prompt():
    """更新测试点生成 Prompt"""
    print("=" * 60)
    print("更新测试点生成 Prompt 配置")
    print("=" * 60)
    
    # 新的 Prompt 配置
    new_prompt = """你是一个专业的保险行业测试专家。请从需求文档中识别所有测试点。

测试点应该包括：
1. 功能性测试点
2. 边界条件测试点
3. 异常情况测试点
4. 业务规则验证点

请以JSON格式返回测试点列表，每个测试点包含：
- title: 测试点标题
- description: 详细描述
- category: 分类（功能/边界/异常/业务规则）
- priority: 优先级（high/medium/low）
- business_line: 业务线（contract-契约/preservation-保全/claim-理赔），根据需求内容判断属于哪个业务线

返回格式示例：
[
  {{"title": "测试点1", "description": "描述1", "category": "功能", "priority": "high", "business_line": "contract"}},
  {{"title": "测试点2", "description": "描述2", "category": "边界", "priority": "medium", "business_line": "preservation"}}
]

{feedback_instruction}"""
    
    # 创建数据库连接
    engine = create_engine(str(settings.DATABASE_URL))
    
    try:
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                # 1. 检查配置是否存在
                print("\n1. 检查 TEST_POINT_PROMPT 配置...")
                result = conn.execute(text("""
                    SELECT id, config_value 
                    FROM system_configs 
                    WHERE config_key = 'TEST_POINT_PROMPT'
                """))
                
                row = result.fetchone()
                
                if row:
                    config_id = row[0]
                    old_value = row[1]
                    print(f"   ✅ 找到配置 (ID: {config_id})")
                    print(f"\n   旧配置预览:")
                    print(f"   {old_value[:200]}...")
                    
                    # 2. 更新配置
                    print("\n2. 更新配置...")
                    conn.execute(
                        text("""
                            UPDATE system_configs 
                            SET config_value = :new_value 
                            WHERE config_key = 'TEST_POINT_PROMPT'
                        """),
                        {"new_value": new_prompt}
                    )
                    print("   ✅ 配置更新成功")
                    
                else:
                    # 3. 创建配置
                    print("   ⚠️  配置不存在，创建新配置...")
                    conn.execute(
                        text("""
                            INSERT INTO system_configs (config_key, config_value, description)
                            VALUES ('TEST_POINT_PROMPT', :new_value, '测试点生成 Prompt')
                        """),
                        {"new_value": new_prompt}
                    )
                    print("   ✅ 配置创建成功")
                
                # 4. 验证更新结果
                print("\n3. 验证更新结果...")
                result = conn.execute(text("""
                    SELECT config_value 
                    FROM system_configs 
                    WHERE config_key = 'TEST_POINT_PROMPT'
                """))
                
                row = result.fetchone()
                if row and 'business_line' in row[0]:
                    print("   ✅ 验证成功: 配置包含 business_line 字段")
                    print(f"\n   新配置预览:")
                    print(f"   {row[0][:300]}...")
                else:
                    print("   ❌ 验证失败: 配置不包含 business_line 字段")
                    trans.rollback()
                    return
                
                # 提交事务
                trans.commit()
                
                print("\n" + "=" * 60)
                print("✅ 更新成功完成!")
                print("=" * 60)
                print("\n说明:")
                print("- TEST_POINT_PROMPT 配置已更新")
                print("- 新配置包含 business_line 字段识别")
                print("- AI 现在会自动识别测试点的业务线")
                print("- 支持的业务线: contract(契约), preservation(保全), claim(理赔)")
                print("\n下次生成测试点时将自动识别业务线!")
                
            except Exception as e:
                trans.rollback()
                print(f"\n❌ 更新失败: {str(e)}")
                raise
                
    except Exception as e:
        print(f"\n❌ 数据库连接失败: {str(e)}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        update_prompt()
    except Exception as e:
        print(f"\n执行失败: {str(e)}")
        sys.exit(1)
