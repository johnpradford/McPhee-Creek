@echo off
echo ====================================
echo McPhee Dashboard - DIAGNOSTIC MODE
echo ====================================
echo.

echo Current Directory:
cd
echo.

echo Files in this directory:
dir *.py
echo.

echo Checking if mcphee_app.py exists:
if exist mcphee_app.py (
    echo [OK] mcphee_app.py FOUND
) else (
    echo [ERROR] mcphee_app.py NOT FOUND
)
echo.

echo Python version:
python --version
echo.

echo Streamlit version:
streamlit --version
echo.

echo Testing Python import:
python -c "import sys; print('Python can run')"
echo.

echo Press any key to try running the dashboard...
pause

echo.
echo Attempting to run dashboard...
streamlit run mcphee_app.py

pause
