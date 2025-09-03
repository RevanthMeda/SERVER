@echo off
REM Production startup script for Windows Server
REM SAT Report Generator - Domain Security Enabled

echo ================================================
echo SAT Report Generator - Production Deployment
echo Server: 172.16.18.21
echo Domain: automation-reports.mobilehmi.org
echo Port: 80 (Requires Administrator)
echo ================================================

REM Set production environment variables
set FLASK_ENV=production
set DEBUG=False
set PORT=80
set ALLOWED_DOMAINS=automation-reports.mobilehmi.org
set SERVER_IP=172.16.18.21
set BLOCK_IP_ACCESS=True

REM Email configuration (update with your details)
set SMTP_SERVER=smtp.gmail.com
set SMTP_PORT=587
set SMTP_USERNAME=meda.revanth@gmail.com
set SMTP_PASSWORD=rleg tbhv rwvb kdus
set DEFAULT_SENDER=meda.revanth@gmail.com
set ENABLE_EMAIL_NOTIFICATIONS=True

REM Security settings
set SECRET_KEY=your-production-secret-key-change-this-immediately
set SESSION_COOKIE_SECURE=True
set WTF_CSRF_ENABLED=True
set PERMANENT_SESSION_LIFETIME=7200

echo Environment variables set for production...
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as Administrator: YES
) else (
    echo WARNING: Not running as Administrator!
    echo Port 80 requires administrator privileges.
    echo Please run this script as Administrator.
    echo.
    echo Alternative: Use port 8080 instead:
    echo   set PORT=8080
    echo   Then configure IIS/Apache to forward port 80 to 8080
    pause
    exit /b 1
)

echo.
echo Starting SAT Report Generator in Production Mode...
echo Domain-only access enabled - IP access blocked
echo.

REM Start the application
python deploy.py

pause