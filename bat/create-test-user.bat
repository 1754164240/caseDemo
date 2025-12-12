@echo off
chcp 65001 >nul
echo ========================================
echo 创建测试用户
echo ========================================
echo.

cd backend

REM 激活虚拟环境
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM 运行脚本
python -m scripts.create_test_user

echo.
pause
