@echo off
setlocal

set "ROOT=%~dp0"

echo Starting backend server (http://localhost:8000)...
start "FinAgents Backend" cmd /k "cd /d "%ROOT%backend" && "%ROOT%.venv\Scripts\python.exe" -m backend.api"

echo Starting frontend dev server (http://localhost:5173)...
start "FinAgents Frontend" cmd /k "cd /d "%ROOT%UI" && npm run dev"

echo Waiting for servers to come up...
timeout /t 5 /nobreak >nul

echo Opening frontend in your browser...
start "" "http://localhost:5173"

endlocal
