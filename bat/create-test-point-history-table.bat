@echo off
chcp 65001 >nul
echo ================================================================================
echo Create test_point_histories table
echo ================================================================================
echo.

cd /d "%~dp0..\backend"

echo Running migration script...
python -m scripts.run_test_point_history_migration

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo Done. Test point history table is ready.
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo Failed. Please review the error output above.
    echo ================================================================================
)

echo.
pause
