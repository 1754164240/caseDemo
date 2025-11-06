@echo off
chcp 65001 >nul
echo ========================================
echo 后端配置一键修复脚本
echo ========================================
echo.

cd backend

REM 检查虚拟环境
if exist ".venv\Scripts\activate.bat" (
    echo [信息] 使用虚拟环境: .venv
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo [信息] 使用虚拟环境: venv
    call venv\Scripts\activate.bat
) else (
    echo [警告] 未找到虚拟环境
    echo.
    choice /C YN /M "是否创建虚拟环境"
    if errorlevel 2 goto :skip_venv
    if errorlevel 1 goto :create_venv
)
goto :check_env

:create_venv
echo [执行] 创建虚拟环境...
python -m venv .venv
if errorlevel 1 (
    echo [错误] 虚拟环境创建失败
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat
echo [成功] 虚拟环境已创建并激活
echo.

:skip_venv
echo [继续] 使用全局 Python 环境
echo.

:check_env
REM 修复 .env 文件
echo [执行] 检查并修复 .env 文件...
python fix_env.py
if errorlevel 1 (
    echo [错误] .env 文件修复失败
    pause
    exit /b 1
)
echo.

REM 检查配置
echo [执行] 验证配置...
python check_config.py
if errorlevel 1 (
    echo.
    echo [错误] 配置验证失败
    echo.
    echo 请检查以上错误信息并手动修复
    pause
    exit /b 1
)
echo.

echo ========================================
echo 修复完成！
echo ========================================
echo.
echo 下一步:
echo 1. 确保 Docker 容器正在运行: docker-compose up -d
echo 2. 启动后端服务: python main.py
echo.
pause

