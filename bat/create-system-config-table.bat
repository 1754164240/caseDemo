@echo off
chcp 65001 >nul
echo ========================================
echo 创建 system_configs 表
echo ========================================
echo.

cd backend

echo 激活虚拟环境...
call .venv\Scripts\activate.bat

echo.
echo 运行数据库迁移脚本...
python -m scripts.create_system_config_table

echo.
echo ========================================
echo 完成
echo ========================================
pause
