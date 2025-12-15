@echo off
REM RF Performance Tool - Startup Script
REM Checks dependencies, installs if needed, and starts both frontend and backend

echo ========================================
echo RF Performance Tool - Starting...
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/6] Python found
python --version

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

echo [2/6] Node.js found
node --version

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo [3/6] Creating Python virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
) else (
    echo [3/6] Virtual environment exists
)

REM Verify virtual environment Python exists
echo [4/6] Checking virtual environment...
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment Python not found
    pause
    exit /b 1
)

REM Check if key Python dependencies are installed
echo [5/6] Checking Python dependencies...
.venv\Scripts\python.exe -c import fastapi >nul 2>&1
if errorlevel 1 goto install_deps
.venv\Scripts\python.exe -c import uvicorn >nul 2>&1
if errorlevel 1 goto install_deps
.venv\Scripts\python.exe -c import sqlalchemy >nul 2>&1
if errorlevel 1 goto install_deps
echo       Python dependencies already installed
.venv\Scripts\python.exe -c import multipart >nul 2>&1
if errorlevel 1 (
    echo       Installing python-multipart (required for file uploads)...
    .venv\Scripts\pip.exe install python-multipart
)
goto deps_done

:install_deps
echo       Installing Python dependencies...
.venv\Scripts\pip.exe install -r backend\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

:deps_done

REM Check if frontend node_modules exists
if not exist "frontend\node_modules" (
    echo [6/6] Installing frontend dependencies...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        cd ..
        pause
        exit /b 1
    )
    cd ..
) else (
    echo [6/6] Frontend dependencies already installed
)

echo.
echo ========================================
echo All dependencies ready!
echo ========================================
echo.
echo Starting backend server...
echo Backend will be available at: http://127.0.0.1:8000
echo API docs will be available at: http://127.0.0.1:8000/docs
echo.

REM Get the current directory
set SCRIPT_DIR=%~dp0

REM Start backend in a new window
start "RF Tool - Backend Server" cmd /k "cd /d %SCRIPT_DIR% && .venv\Scripts\python.exe -m uvicorn backend.src.api.main:app --host 127.0.0.1 --port 8000 --reload"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

echo Starting frontend dev server...
echo Frontend will be available at: http://127.0.0.1:5173
echo.

REM Start frontend in a new window
start "RF Tool - Frontend Dev Server" cmd /k "cd /d %SCRIPT_DIR%frontend && npm run dev"

echo.
echo ========================================
echo Both servers are starting!
echo ========================================
echo.
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://127.0.0.1:5173
echo.
echo Two new windows have opened - one for backend, one for frontend.
echo Close those windows to stop the servers.
echo.
echo Press any key to exit this window (servers will continue running)...
pause >nul
