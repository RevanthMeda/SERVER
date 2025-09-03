@echo off
echo ================================================
echo Quick Restart and Redeploy
echo ================================================

echo Step 1: Deploying updated files to IIS...
call deploy_to_iis.bat

echo.
echo Step 2: Please stop the Flask backend (press Ctrl+C in the other window)
echo Step 3: Then run start_backend_service.bat
echo Step 4: Access https://automation-reports.mobilehmi.org

echo.
echo The internal server error should now be resolved!
pause