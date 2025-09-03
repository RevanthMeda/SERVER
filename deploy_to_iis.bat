@echo off
echo ================================================
echo SAT Report Generator - IIS Deployment
echo ================================================

set IIS_PATH=C:\inetpub\wwwroot\REPORT_GENERATOR
set SOURCE_PATH=%~dp0iis_files

echo Deploying files to IIS directory...
echo Source: %SOURCE_PATH%
echo Target: %IIS_PATH%
echo.

REM Check if IIS directory exists
if not exist "%IIS_PATH%" (
    echo Creating IIS directory: %IIS_PATH%
    mkdir "%IIS_PATH%"
)

REM Copy files to IIS
echo Copying index.html...
copy "%SOURCE_PATH%\index.html" "%IIS_PATH%\index.html" /Y

echo Copying web.config...
copy "%SOURCE_PATH%\web.config" "%IIS_PATH%\web.config" /Y

echo.
echo ================================================
echo Deployment completed!
echo ================================================
echo.
echo Files deployed to: %IIS_PATH%
echo.
echo Next steps:
echo 1. Start the backend service: start_backend_service.bat
echo 2. Ensure IIS site is running
echo 3. Access: https://automation-reports.mobilehmi.org
echo.

pause