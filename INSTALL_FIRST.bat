@echo off
echo ====================================
echo McPhee Dashboard - First Time Setup
echo ====================================
echo.
echo This will install required Python packages...
echo.

pip install streamlit pandas numpy openpyxl xlrd python-dateutil matplotlib --break-system-packages

echo.
echo ====================================
echo Installation Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Close this window
echo 2. Double-click RUN_DASHBOARD.bat to start the dashboard
echo.

pause
