@echo off
echo ========================================
echo 智能测试用例平台 - 环境配置脚本
echo ========================================
echo.

REM 检查 .env 文件是否存在
if exist "backend\.env" (
    echo [信息] backend\.env 文件已存在
    echo.
    choice /C YN /M "是否要重新创建 .env 文件（会覆盖现有文件）"
    if errorlevel 2 goto :skip_env
    if errorlevel 1 goto :create_env
) else (
    goto :create_env
)

:create_env
echo [执行] 创建 backend\.env 文件...
copy "backend\.env.example" "backend\.env" >nul
if errorlevel 1 (
    echo [错误] 无法创建 .env 文件
    pause
    exit /b 1
)
echo [成功] 已创建 backend\.env 文件
echo.
echo ========================================
echo 重要提示：
echo ========================================
echo 1. 请编辑 backend\.env 文件
echo 2. 必须配置 OPENAI_API_KEY
echo 3. 确认 DATABASE_URL 格式正确
echo.
echo 示例配置：
echo   OPENAI_API_KEY=sk-your-api-key-here
echo   DATABASE_URL=postgresql+psycopg://testcase:testcase123@localhost:5432/test_case_db
echo.
goto :end

:skip_env
echo [跳过] 保留现有 .env 文件
echo.

:end
echo ========================================
echo 配置完成！
echo ========================================
echo.
echo 下一步：
echo 1. 编辑 backend\.env 文件配置 API Key
echo 2. 运行 docker-compose up -d 启动数据库
echo 3. 运行 install-backend.bat 安装依赖
echo 4. 运行 start-backend.bat 启动后端
echo.
pause

