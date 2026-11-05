@echo off
echo Installing dependencies...
pip install -r "%~dp0backend\requirements.txt"
echo.
echo Done! Now starting server...
cd /d "%~dp0backend"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
