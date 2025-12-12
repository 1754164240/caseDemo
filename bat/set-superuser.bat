@echo off
chcp 65001 >nul
echo ========================================
echo 设置超级管理员
echo ========================================
echo.

cd backend

echo 激活虚拟环境...
call .\.venv\Scripts\activate.bat

echo.
echo 当前用户列表:
echo.
python -m scripts.set_superuser

echo.
echo ========================================
echo.
set /p username=请输入要设置为超级管理员的用户名: 

if "%username%"=="" (
    echo 错误: 用户名不能为空
    pause
    exit /b 1
)

echo.
echo 正在设置用户 '%username%' 为超管...
python -m scripts.set_superuser %username%

echo.
echo ========================================
echo 完成
echo ========================================
echo.
echo 提示: 如果设置成功，请重新登录以获取新的权限
echo.
pause
