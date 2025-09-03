@echo off
echo ================================================
echo SAT Report Generator - Administrator Launch
echo ================================================

echo Checking for Administrator privileges...

net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Administrator privileges confirmed
    echo.
    goto :run_server
) else (
    echo ❌ This script requires Administrator privileges
    echo.
    echo Please follow these steps:
    echo 1. Right-click on Command Prompt
    echo 2. Select "Run as administrator"
    echo 3. Navigate to your project directory
    echo 4. Run: start_as_admin.bat
    echo.
    echo Or use PowerShell as Administrator:
    echo PowerShell: Start-Process cmd -ArgumentList '/c start_backend_service.bat' -Verb RunAs
    echo.
    pause
    exit /b 1
)

:run_server
cd /d "E:\report generator\SERVER"

echo Starting Flask HTTPS server on port 443...
echo.
echo Configuration:
echo - HTTPS Server: https://automation-reports.mobilehmi.org:443
echo - Direct access (no IIS needed)
echo - SSL/TLS encryption: Required
echo - Administrator mode: ENABLED
echo.

echo Starting HTTPS server with Administrator privileges...
python run_local_backend.py

pause