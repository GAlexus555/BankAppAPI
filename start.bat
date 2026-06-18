@echo off
echo Installing dependencies...
pip install fastapi uvicorn sqlalchemy "pydantic[email]" "python-jose[cryptography]" "passlib[bcrypt]" fastapi-restful python-multipart

echo.
echo Initializing database...
python init_db.py

echo.
echo Starting API...
uvicorn src.main:app --reload
pause
