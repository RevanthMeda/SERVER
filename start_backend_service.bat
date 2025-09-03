@echo off
echo ================================================
echo SAT Report Generator - IIS Backend Service
echo ================================================

cd /d "E:\report generator\SERVER"

echo Starting Flask backend for IIS reverse proxy...
echo.
echo Configuration:
echo - IIS Frontend: https://automation-reports.mobilehmi.org:443
echo - Flask Backend: http://127.0.0.1:8080
echo - IIS handles HTTPS, routes to Flask
echo - Corporate hosting setup
echo.

echo Starting backend service...
python run_local_backend.py

pause