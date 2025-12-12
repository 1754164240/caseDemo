"""
自动修复 .env 文件格式
"""
import os
import re
from pathlib import Path

print("=" * 60)
print("环境配置修复脚本")
print("=" * 60)
print()

env_file = Path(".env")

if not env_file.exists():
    print("❌ .env 文件不存在")
    print()
    
    if Path(".env.example").exists():
        print("正在从 .env.example 创建 .env 文件...")
        import shutil
        shutil.copy(".env.example", ".env")
        print("✅ 已创建 .env 文件")
        print()
        print("请编辑 .env 文件，配置 OPENAI_API_KEY")
    else:
        print("❌ .env.example 文件也不存在")
        print("请手动创建 .env 文件")
    
    exit(0)

print("正在检查 .env 文件...")
print()

# 读取文件
with open(env_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

modified = False
new_lines = []

for i, line in enumerate(lines, 1):
    original_line = line
    
    # 修复 DATABASE_URL
    if line.strip().startswith('DATABASE_URL='):
        if 'postgresql://' in line and 'postgresql+psycopg://' not in line:
            line = line.replace('postgresql://', 'postgresql+psycopg://')
            print(f"✏️  第 {i} 行: 修复 DATABASE_URL 格式")
            print(f"   旧: {original_line.strip()}")
            print(f"   新: {line.strip()}")
            print()
            modified = True
    
    # 修复 CORS_ORIGINS (移除 JSON 格式)
    if line.strip().startswith('CORS_ORIGINS='):
        # 检查是否是 JSON 数组格式
        if '[' in line and ']' in line:
            # 提取 URL
            urls = re.findall(r'https?://[^"]+', line)
            if urls:
                new_value = ','.join(urls)
                line = f'CORS_ORIGINS={new_value}\n'
                print(f"✏️  第 {i} 行: 修复 CORS_ORIGINS 格式")
                print(f"   旧: {original_line.strip()}")
                print(f"   新: {line.strip()}")
                print()
                modified = True
    
    new_lines.append(line)

if modified:
    # 备份原文件
    backup_file = env_file.with_suffix('.env.backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"✅ 已备份原文件到: {backup_file}")
    print()
    
    # 写入修复后的文件
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("✅ 已修复 .env 文件")
    print()
    
    print("修复内容:")
    print("-" * 60)
    for line in new_lines:
        if line.strip() and not line.strip().startswith('#'):
            # 隐藏敏感信息
            if 'API_KEY' in line or 'SECRET' in line or 'PASSWORD' in line:
                key = line.split('=')[0]
                print(f"{key}=***隐藏***")
            else:
                print(line.strip())
    print("-" * 60)
    print()
else:
    print("✅ .env 文件格式正确，无需修复")
    print()

print("=" * 60)
print("完成！")
print("=" * 60)
print()
print("下一步:")
print("1. 检查配置: python -m scripts.check_config")
print("2. 启动服务: python -m scripts.main")
