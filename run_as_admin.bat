@echo off
echo ================================================
echo SAT Report Generator - Administrator Check
echo ================================================

REM Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Administrator privileges confirmed
    echo.
    goto :run_app
) else (
    echo ❌ Administrator privileges required for port 443
    echo.
    echo Please follow these steps:
    echo 1. Right-click on PowerShell or Command Prompt
    echo 2. Select "Run as administrator"
    echo 3. Navigate to: cd "E:\report generator\SERVER"
    echo 4. Run: python app.py
    echo.
    echo Or double-click this file as Administrator:
    echo Right-click run_as_admin.bat → "Run as administrator"
    echo.
    pause
    exit /b 1
)

:run_app
echo Starting SAT Report Generator on port 443...
echo.
cd /d "E:\report generator\SERVER"
python app.py
pause