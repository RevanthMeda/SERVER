@echo off
echo ================================================
echo SAT Report Generator - Backend Service Startup
echo ================================================

cd /d "E:\report generator\SERVER"

echo Starting Flask backend service...
echo.
echo Configuration:
echo - Backend Service: http://127.0.0.1:8080
echo - IIS Frontend: https://automation-reports.mobilehmi.org:443
echo - Mode: Production backend for IIS integration
echo.

echo Initializing backend service...
python run_local_backend.py

pause