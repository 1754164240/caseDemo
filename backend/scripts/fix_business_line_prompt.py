"""
修复 TEST_POINT_PROMPT 配置，添加 business_line 字段
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

# 新的 Prompt 模板（包含 business_line）
NEW_PROMPT = """你是一个专业的保险行业测试专家。请从需求文档中识别所有测试点。

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
  {{"title": "测试点1", "description": "描述1", "category": "功能", "priority": "high", "business_line": "contract-契约"}},
  {{"title": "测试点2", "description": "描述2", "category": "边界", "priority": "medium", "business_line": "preservation-保全"}}
]

{feedback_instruction}"""


def main():
    print("=" * 70)
    print("修复 TEST_POINT_PROMPT 配置 - 添加 business_line 字段")
    print("=" * 70)
    
    try:
        # 创建数据库连接
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.begin() as conn:
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
                
                # 检查是否已包含 business_line
                if 'business_line' in old_value:
                    print("   ℹ️  配置已包含 business_line 字段，无需更新")
                    return
                
                print(f"\n   旧配置预览:")
                print(f"   {old_value[:200]}...")
                
                # 2. 更新配置
                print("\n2. 更新配置...")
                conn.execute(
                    text("""
                        UPDATE system_configs 
                        SET config_value = :new_value,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE config_key = 'TEST_POINT_PROMPT'
                    """),
                    {"new_value": NEW_PROMPT}
                )
                print("   ✅ 配置更新成功")
                
            else:
                # 3. 创建配置
                print("   ⚠️  配置不存在，创建新配置...")
                conn.execute(
                    text("""
                        INSERT INTO system_configs (config_key, config_value, description, created_at)
                        VALUES ('TEST_POINT_PROMPT', :new_value, '测试点生成 Prompt', CURRENT_TIMESTAMP)
                    """),
                    {"new_value": NEW_PROMPT}
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
                return
        
        print("\n" + "=" * 70)
        print("✅ 修复完成！")
        print("=" * 70)
        print("\n提示:")
        print("1. 重启后端服务以使配置生效")
        print("2. 新生成的测试点将包含 business_line 字段")
        print("3. 生成测试用例时会根据 business_line 选择对应的 Prompt")
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
