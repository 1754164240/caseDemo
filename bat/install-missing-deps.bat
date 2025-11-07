@echo off
chcp 65001 >nul
echo ========================================
echo 安装缺失的依赖包
echo ========================================
echo.

cd backend

REM 检查虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo [信息] 激活虚拟环境: .venv
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [信息] 激活虚拟环境: venv
    call venv\Scripts\activate.bat
) else (
    echo [警告] 未找到虚拟环境，使用全局 Python
)
echo.

echo [执行] 安装/更新依赖包...
echo.

REM 升级 pip
python -m pip install --upgrade pip

REM 安装所有依赖
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [错误] 依赖安装失败
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.

REM 运行配置检查
echo [执行] 验证安装...
python check_config.py

echo.
pause

