@echo off
cd /d "%~dp0"
where python >nul 2>nul || (
  echo Python 3.11 or newer is required.
  exit /b 1
)
where npm >nul 2>nul || (
  echo Node.js and npm are required.
  exit /b 1
)
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
if not exist .env copy .env.example .env
pushd frontend
call npm install
popd
echo.
echo Setup complete. Start the system with run.bat
echo Then open http://127.0.0.1:5173
