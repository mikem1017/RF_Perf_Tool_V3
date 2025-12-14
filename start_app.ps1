# RF Performance Tool - Startup Script (PowerShell)
# Checks dependencies, installs if needed, and starts both frontend and backend

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RF Performance Tool - Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "[1/6] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "       Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Node.js is installed
Write-Host "[2/6] Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Node.js not found"
    }
    Write-Host "       Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Node.js is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Create virtual environment if it doesn't exist
Write-Host "[3/6] Checking Python virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    Write-Host "       Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "       Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "       Virtual environment exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "[4/6] Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to activate virtual environment" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "       Virtual environment activated" -ForegroundColor Green

# Check if key Python dependencies are installed
Write-Host "[5/6] Checking Python dependencies..." -ForegroundColor Yellow
try {
    python -c "import fastapi, uvicorn, sqlalchemy" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Dependencies not installed"
    }
    Write-Host "       Python dependencies already installed" -ForegroundColor Green
    
    # Still check for python-multipart specifically
    python -c "import multipart" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "       Installing python-multipart (required for file uploads)..." -ForegroundColor Yellow
        pip install python-multipart
    }
} catch {
    Write-Host "       Installing Python dependencies..." -ForegroundColor Yellow
    pip install -r backend\requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install Python dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "       Python dependencies installed" -ForegroundColor Green
}

# Check if frontend node_modules exists
Write-Host "[6/6] Checking frontend dependencies..." -ForegroundColor Yellow
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "       Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location frontend
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install frontend dependencies" -ForegroundColor Red
        Pop-Location
        Read-Host "Press Enter to exit"
        exit 1
    }
    Pop-Location
    Write-Host "       Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "       Frontend dependencies already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "All dependencies ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting backend server..." -ForegroundColor Yellow
Write-Host "Backend will be available at: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "API docs will be available at: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Get the current directory
$scriptPath = Get-Location

# Start backend in a new window
$backendScript = "cd /d `"$scriptPath`" && call .venv\Scripts\activate.bat && python -m backend.src.main"
Start-Process cmd -ArgumentList "/k", $backendScript -WindowStyle Normal

# Wait a moment for backend to start
Start-Sleep -Seconds 3

Write-Host "Starting frontend dev server..." -ForegroundColor Yellow
Write-Host "Frontend will be available at: http://127.0.0.1:5173" -ForegroundColor Cyan
Write-Host ""

# Start frontend in a new window
$frontendScript = "cd /d `"$scriptPath\frontend`" && npm run dev"
Start-Process cmd -ArgumentList "/k", $frontendScript -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Both servers are starting!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "Frontend: http://127.0.0.1:5173" -ForegroundColor Yellow
Write-Host ""
Write-Host "Two new windows have opened - one for backend, one for frontend." -ForegroundColor Cyan
Write-Host "Close those windows to stop the servers." -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Enter to exit this window (servers will continue running)..." -ForegroundColor Gray
Read-Host
