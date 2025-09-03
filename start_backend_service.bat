@echo off
echo ================================================
echo SAT Report Generator - Direct HTTPS Server
echo ================================================

cd /d "E:\report generator\SERVER"

echo Starting Flask HTTPS server on port 443...
echo.
echo Configuration:
echo - HTTPS Server: https://automation-reports.mobilehmi.org:443
echo - Direct access (no IIS needed)
echo - SSL/TLS encryption: Required
echo - Mode: Production HTTPS server
echo.

echo IMPORTANT: This requires Administrator privileges for port 443
echo If you get "Permission denied", run Command Prompt as Administrator
echo.

echo Starting HTTPS server...
python run_local_backend.py

pause