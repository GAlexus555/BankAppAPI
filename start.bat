@echo off
echo Installing dependencies...
pip install fastapi uvicorn sqlalchemy "pydantic[email]" "python-jose[cryptography]" "passlib[bcrypt]" fastapi-restful python-multipart

echo.
echo Initializing database...
python init_db.py

echo.
echo Starting API...
set PYTHONPATH=src
python -m uvicorn src.main:app --reload
pause
