"""
创建测试用户脚本
"""
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from app.db.base import import_models

# 导入所有模型
import_models()

def create_test_user():
    """创建测试用户"""
    db = SessionLocal()
    
    try:
        # 检查用户是否已存在
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            print("✅ 测试用户已存在")
            print(f"   用户名: admin")
            print(f"   邮箱: {existing_user.email}")
            return
        
        # 创建测试用户
        user = User(
            username="admin",
            email="admin@example.com",
            full_name="管理员",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print("=" * 60)
        print("✅ 测试用户创建成功！")
        print("=" * 60)
        print()
        print("登录信息:")
        print(f"  用户名: admin")
        print(f"  密码: admin123")
        print(f"  邮箱: admin@example.com")
        print()
        print("请使用以上信息登录系统")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 创建用户失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_user()

