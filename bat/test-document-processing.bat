@echo off
chcp 65001 >nul
echo ========================================
echo 测试文档处理功能
echo ========================================
echo.

cd backend

REM 激活虚拟环境
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo 选择测试类型:
echo 1. 测试文档解析和 AI 提取
echo 2. 测试 OpenAI API 连接
echo.
choice /C 12 /M "请选择"

if errorlevel 2 goto :test_api
if errorlevel 1 goto :test_doc

:test_doc
echo.
echo [执行] 测试文档处理...
echo.
python -m scripts.test_document_processing
goto :end

:test_api
echo.
echo [执行] 测试 OpenAI API 连接...
echo.
python -m scripts.test_document_processing api
goto :end

:end
echo.
pause
