"""
执行业务线字段迁移
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings


def run_migration():
    """执行业务线字段迁移"""
    print("=" * 60)
    print("开始执行业务线字段迁移")
    print("=" * 60)
    
    # 创建数据库连接
    engine = create_engine(str(settings.DATABASE_URL))
    
    try:
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                # 1. 检查字段是否已存在
                print("\n1. 检查 business_line 字段是否已存在...")
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'test_points' 
                    AND column_name = 'business_line'
                """))
                
                if result.fetchone():
                    print("   ⚠️  business_line 字段已存在，跳过迁移")
                    trans.rollback()
                    return
                
                # 2. 添加 business_line 字段
                print("\n2. 添加 business_line 字段到 test_points 表...")
                conn.execute(text("""
                    ALTER TABLE test_points 
                    ADD COLUMN business_line VARCHAR(50)
                """))
                print("   ✅ business_line 字段添加成功")
                
                # 3. 添加注释
                print("\n3. 添加字段注释...")
                conn.execute(text("""
                    COMMENT ON COLUMN test_points.business_line 
                    IS '业务线：contract(契约)/preservation(保全)/claim(理赔)'
                """))
                print("   ✅ 字段注释添加成功")
                
                # 4. 验证迁移结果
                print("\n4. 验证迁移结果...")
                result = conn.execute(text("""
                    SELECT 
                        column_name,
                        data_type,
                        character_maximum_length,
                        is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'test_points' 
                    AND column_name = 'business_line'
                """))
                
                row = result.fetchone()
                if row:
                    print(f"   ✅ 字段验证成功:")
                    print(f"      - 字段名: {row[0]}")
                    print(f"      - 数据类型: {row[1]}")
                    print(f"      - 最大长度: {row[2]}")
                    print(f"      - 可为空: {row[3]}")
                else:
                    print("   ❌ 字段验证失败")
                    trans.rollback()
                    return
                
                # 5. 查询现有测试点数量
                print("\n5. 查询现有测试点数量...")
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM test_points
                """))
                count = result.fetchone()[0]
                print(f"   ℹ️  现有测试点数量: {count}")
                
                # 提交事务
                trans.commit()
                
                print("\n" + "=" * 60)
                print("✅ 迁移成功完成!")
                print("=" * 60)
                print("\n说明:")
                print("- business_line 字段已添加到 test_points 表")
                print("- 现有测试点的 business_line 字段为 NULL")
                print("- 新生成的测试点将自动识别并保存业务线信息")
                print("- 支持的业务线: contract(契约), preservation(保全), claim(理赔)")
                
            except Exception as e:
                trans.rollback()
                print(f"\n❌ 迁移失败: {str(e)}")
                raise
                
    except Exception as e:
        print(f"\n❌ 数据库连接失败: {str(e)}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"\n执行失败: {str(e)}")
        sys.exit(1)

