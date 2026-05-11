@echo off
pushd "%~dp0"

echo ====================================
echo McPhee Wildlife Monitoring Dashboard
echo ====================================
echo.
echo Current directory: %CD%
echo.
echo Starting dashboard...
echo Your browser will open automatically.
echo.
echo To stop the dashboard, close this window or press Ctrl+C
echo.

streamlit run mcphee_app.py

popd
pause
