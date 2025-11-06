"""
设置用户为超级管理员的脚本
"""
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

def set_superuser(username: str):
    """设置用户为超级管理员"""
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # 检查用户是否存在
            result = conn.execute(
                text("SELECT id, username, is_superuser FROM users WHERE username = :username"),
                {"username": username}
            )
            user = result.fetchone()
            
            if not user:
                print(f"❌ 用户 '{username}' 不存在")
                print()
                print("可用的用户列表:")
                result = conn.execute(text("SELECT username, email, is_superuser FROM users"))
                users = result.fetchall()
                for u in users:
                    superuser_status = "✅ 超级管理员" if u[2] else "❌ 普通用户"
                    print(f"  - {u[0]} ({u[1]}) - {superuser_status}")
                return False
            
            if user[2]:
                print(f"✅ 用户 '{username}' 已经是超级管理员")
                return True
            
            # 设置为超级管理员
            conn.execute(
                text("UPDATE users SET is_superuser = true WHERE username = :username"),
                {"username": username}
            )
            conn.commit()
            
            print(f"✅ 成功将用户 '{username}' 设置为超级管理员")
            return True
            
    except Exception as e:
        print(f"❌ 操作失败: {str(e)}")
        return False
    finally:
        engine.dispose()


def list_users():
    """列出所有用户"""
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT username, email, is_superuser, is_active FROM users ORDER BY id")
            )
            users = result.fetchall()
            
            if not users:
                print("❌ 没有找到任何用户")
                return
            
            print("用户列表:")
            print("-" * 80)
            print(f"{'用户名':<20} {'邮箱':<30} {'超级管理员':<15} {'状态':<10}")
            print("-" * 80)
            
            for user in users:
                username = user[0]
                email = user[1]
                is_superuser = "✅ 是" if user[2] else "❌ 否"
                is_active = "✅ 活跃" if user[3] else "❌ 禁用"
                print(f"{username:<20} {email:<30} {is_superuser:<15} {is_active:<10}")
            
            print("-" * 80)
            
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    print("=" * 80)
    print("设置超级管理员")
    print("=" * 80)
    print()
    
    if len(sys.argv) > 1:
        username = sys.argv[1]
        set_superuser(username)
    else:
        print("当前系统中的用户:")
        print()
        list_users()
        print()
        print("使用方法:")
        print("  python set_superuser.py <username>")
        print()
        print("示例:")
        print("  python set_superuser.py admin")
    
    print()
    print("=" * 80)

