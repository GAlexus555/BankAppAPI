@echo off
cd /d "%~dp0"

echo ============================================================
echo   BankApp API - Starter
echo ============================================================
echo.

echo Checking Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo FEHLER: Python ist nicht installiert!
    echo Bitte Python installieren: https://www.python.org/downloads/
    echo Wichtig: "Add Python to PATH" aktivieren beim Installieren!
    pause
    exit /b
)
echo Python OK.
echo.

echo [1/3] Installing dependencies...
python -m pip install fastapi uvicorn sqlalchemy "pydantic[email]" "python-jose[cryptography]" "passlib[bcrypt]" "bcrypt==3.2.2" fastapi-restful typing_inspect python-multipart
if %errorLevel% neq 0 (
    echo.
    echo FEHLER: pip fehlgeschlagen.
    pause
    exit /b
)

echo.
echo [2/3] Initializing database...
python init_db.py
if %errorLevel% neq 0 (
    echo.
    echo FEHLER: Datenbankinitialisierung fehlgeschlagen.
    pause
    exit /b
)

echo.
echo [3/3] Starting API...
echo Freeing port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /f /pid %%a >nul 2>&1

echo.
echo API laeuft auf: http://127.0.0.1:8000
echo Swagger UI:     http://127.0.0.1:8000/docs
echo Stoppen mit:    STRG + C
echo.
set PYTHONPATH=src
python -m uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
pause
