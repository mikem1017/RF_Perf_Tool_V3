@echo off
REM Test entry point script for Windows
REM Runs backend tests with coverage

echo Running backend tests...
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment: .venv
    call .venv\Scripts\activate.bat
) else if exist "backend\.venv\Scripts\activate.bat" (
    echo Activating virtual environment: backend\.venv
    call backend\.venv\Scripts\activate.bat
) else (
    echo No virtual environment found. Using system Python.
    echo.
)

REM Check if pytest is available
python -m pytest --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pytest is not installed or not available.
    echo Please install dependencies: pip install -r backend\requirements.txt
    exit /b 1
)

REM Check if pytest-cov is available
python -c "import pytest_cov" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Coverage reporting available.
    set USE_COV=1
) else (
    echo WARNING: pytest-cov not installed. Running tests without coverage.
    echo Install with: pip install pytest-cov
    set USE_COV=0
)

REM Run pytest
echo Executing tests...
echo.
if %USE_COV%==1 (
    python -m pytest backend\tests\ -v --cov=backend\src --cov-report=term-missing
) else (
    python -m pytest backend\tests\ -v
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Tests completed successfully!
) else (
    echo.
    echo Tests failed!
    exit /b %ERRORLEVEL%
)

