@echo off
chcp 65001 >nul
echo ========================================
echo 智能测试用例平台 - 环境检查脚本
echo ========================================
echo.

set ERROR_COUNT=0

REM 检查 Python
echo [检查] Python 版本...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    set /a ERROR_COUNT+=1
) else (
    python --version
    echo [成功] Python 已安装
)
echo.

REM 检查 Node.js
echo [检查] Node.js 版本...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请先安装 Node.js 18+
    set /a ERROR_COUNT+=1
) else (
    node --version
    echo [成功] Node.js 已安装
)
echo.

REM 检查 Docker
echo [检查] Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [警告] 未找到 Docker，数据库服务将无法启动
    echo [提示] 请安装 Docker Desktop
    set /a ERROR_COUNT+=1
) else (
    docker --version
    echo [成功] Docker 已安装
)
echo.

REM 检查 .env 文件
echo [检查] 环境配置文件...
if exist "backend\.env" (
    echo [成功] backend\.env 文件存在
    
    REM 检查 API Key
    findstr /C:"OPENAI_API_KEY=sk-" "backend\.env" >nul 2>&1
    if errorlevel 1 (
        findstr /C:"OPENAI_API_KEY=your" "backend\.env" >nul 2>&1
        if not errorlevel 1 (
            echo [警告] OPENAI_API_KEY 未配置，请编辑 backend\.env 文件
            set /a ERROR_COUNT+=1
        )
    ) else (
        echo [成功] OPENAI_API_KEY 已配置
    )
    
    REM 检查数据库 URL 格式
    findstr /C:"postgresql+psycopg://" "backend\.env" >nul 2>&1
    if errorlevel 1 (
        echo [警告] DATABASE_URL 格式可能不正确
        echo [提示] 应该使用: postgresql+psycopg://user:pass@host:port/db
        set /a ERROR_COUNT+=1
    ) else (
        echo [成功] DATABASE_URL 格式正确
    )
) else (
    echo [错误] backend\.env 文件不存在
    echo [提示] 运行 setup-env.bat 创建配置文件
    set /a ERROR_COUNT+=1
)
echo.

REM 检查 Docker 容器
echo [检查] Docker 容器状态...
docker ps >nul 2>&1
if errorlevel 1 (
    echo [警告] Docker 未运行或无法连接
    echo [提示] 请启动 Docker Desktop
) else (
    docker ps --filter "name=casedemo1" --format "table {{.Names}}\t{{.Status}}" 2>nul | findstr "casedemo1" >nul
    if errorlevel 1 (
        echo [警告] 数据库容器未运行
        echo [提示] 运行: docker-compose up -d
        set /a ERROR_COUNT+=1
    ) else (
        echo [成功] 数据库容器正在运行
        docker ps --filter "name=casedemo1" --format "table {{.Names}}\t{{.Status}}"
    )
)
echo.

REM 检查后端依赖
echo [检查] 后端依赖...
if exist "backend\.venv" (
    echo [成功] 虚拟环境已创建
) else (
    if exist "backend\venv" (
        echo [成功] 虚拟环境已创建
    ) else (
        echo [警告] 虚拟环境未创建
        echo [提示] 运行: install-backend.bat
        set /a ERROR_COUNT+=1
    )
)
echo.

REM 检查前端依赖
echo [检查] 前端依赖...
if exist "frontend\node_modules" (
    echo [成功] 前端依赖已安装
) else (
    echo [警告] 前端依赖未安装
    echo [提示] 运行: install-frontend.bat
    set /a ERROR_COUNT+=1
)
echo.

REM 总结
echo ========================================
echo 检查完成！
echo ========================================
if %ERROR_COUNT% EQU 0 (
    echo [成功] 所有检查通过，可以启动服务
    echo.
    echo 启动步骤：
    echo 1. 运行: start-backend.bat
    echo 2. 运行: start-frontend.bat
    echo 3. 访问: http://localhost:5173
) else (
    echo [警告] 发现 %ERROR_COUNT% 个问题，请先解决
    echo.
    echo 建议步骤：
    echo 1. 运行: setup-env.bat （配置环境变量）
    echo 2. 运行: docker-compose up -d （启动数据库）
    echo 3. 运行: install-backend.bat （安装后端依赖）
    echo 4. 运行: install-frontend.bat （安装前端依赖）
)
echo.
pause

