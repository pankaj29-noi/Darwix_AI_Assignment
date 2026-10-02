@echo off
cd /d "%~dp0"
if not exist .venv (
  echo Run setup.bat first.
  exit /b 1
)
start "Darwix API" cmd /k "cd /d %~dp0 && call .venv\Scripts\activate.bat && set PYTHONPATH=backend && uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000"
pushd frontend
echo App: http://127.0.0.1:5173
call npm run dev -- --host 127.0.0.1 --port 5173
popd
