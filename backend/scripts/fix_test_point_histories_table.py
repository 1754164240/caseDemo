"""
修复 test_point_histories 表，确保 code 字段存在
"""
import sys
from sqlalchemy import text
from app.db.session import SessionLocal

def fix_test_point_histories_table():
    """检查并添加 code 字段到 test_point_histories 表"""
    db = SessionLocal()
    try:
        print("=" * 60)
        print("检查 test_point_histories 表结构")
        print("=" * 60)
        
        # 检查 code 字段是否存在
        check_sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'test_point_histories' 
        AND column_name = 'code'
        """
        
        result = db.execute(text(check_sql)).fetchone()
        
        if result:
            print("✅ code 字段已存在")
            return True
        
        print("⚠️  code 字段不存在，正在添加...")
        
        # 添加 code 字段
        alter_sql = """
        ALTER TABLE test_point_histories 
        ADD COLUMN code VARCHAR(20)
        """
        
        db.execute(text(alter_sql))
        db.commit()
        
        print("✅ code 字段添加成功")
        
        # 验证字段已添加
        result = db.execute(text(check_sql)).fetchone()
        if result:
            print("✅ 验证成功：code 字段已存在")
            return True
        else:
            print("❌ 验证失败：code 字段仍不存在")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("\n修复 test_point_histories 表\n")
    success = fix_test_point_histories_table()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 修复完成")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ 修复失败")
        print("=" * 60)
        sys.exit(1)

