@echo off
echo Loading environment from .env (if present)...
if exist .env (
  for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
    if not "%%a"=="" set %%a=%%b
  )
)

echo Starting Flask application...
python app.py
pause 