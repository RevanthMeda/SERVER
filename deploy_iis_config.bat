@echo off
echo ================================================
echo SAT Report Generator - IIS Configuration Deploy
echo ================================================

set IIS_PATH=C:\inetpub\wwwroot\REPORT_GENERATOR
set SOURCE_PATH=%~dp0iis_config

echo Deploying IIS configuration files...
echo Source: %SOURCE_PATH%
echo Target: %IIS_PATH%
echo.

REM Check if IIS directory exists
if not exist "%IIS_PATH%" (
    echo Creating IIS directory: %IIS_PATH%
    mkdir "%IIS_PATH%"
)

REM Copy configuration files to IIS
echo Copying web.config...
copy "%SOURCE_PATH%\web.config" "%IIS_PATH%\web.config" /Y

echo Copying error pages...
copy "%SOURCE_PATH%\404.html" "%IIS_PATH%\404.html" /Y
copy "%SOURCE_PATH%\500.html" "%IIS_PATH%\500.html" /Y

echo.
echo ================================================
echo IIS Configuration Deployed Successfully!
echo ================================================
echo.
echo Configuration Details:
echo - web.config: URL Rewrite to proxy Flask backend
echo - Error pages: Custom 404 and 500 error handling
echo - Backend proxy: All requests forwarded to http://127.0.0.1:8080
echo.
echo Next Steps:
echo 1. Ensure IIS URL Rewrite Module is installed
echo 2. Start Flask backend: start_backend_service.bat
echo 3. Verify IIS site is running on port 443
echo 4. Access: https://automation-reports.mobilehmi.org
echo.

pause