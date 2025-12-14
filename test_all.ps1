# Test entry point script for Windows PowerShell
# Runs backend tests with coverage and frontend type checking

Write-Host "=== RF Performance Tool Test Suite ===" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment: .venv" -ForegroundColor Yellow
    & ".venv\Scripts\Activate.ps1"
} elseif (Test-Path "backend\.venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment: backend\.venv" -ForegroundColor Yellow
    & "backend\.venv\Scripts\Activate.ps1"
} else {
    Write-Host "No virtual environment found. Using system Python." -ForegroundColor Yellow
}

# Check if pytest is available
try {
    $pytestVersion = python -m pytest --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: pytest is not installed or not available." -ForegroundColor Red
        Write-Host "Please install dependencies: pip install -r backend\requirements.txt" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "ERROR: Python or pytest not found." -ForegroundColor Red
    Write-Host "Please ensure Python is installed and dependencies are installed." -ForegroundColor Yellow
    exit 1
}

# Check if pytest-cov is available
$hasCov = python -c "import pytest_cov" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Coverage reporting available." -ForegroundColor Green
    $useCoverage = $true
} else {
    Write-Host "WARNING: pytest-cov not installed. Running tests without coverage." -ForegroundColor Yellow
    Write-Host "Install with: pip install pytest-cov" -ForegroundColor Yellow
    $useCoverage = $false
}

# Check if httpx is available for API tests
try {
    python -c "import httpx" > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "httpx found. API tests will run." -ForegroundColor Green
    } else {
        Write-Host "WARNING: httpx not installed. API tests will be skipped." -ForegroundColor Yellow
        Write-Host "Install with: pip install httpx" -ForegroundColor Yellow
    }
} catch {
    Write-Host "WARNING: Could not check httpx. API tests may be skipped." -ForegroundColor Yellow
}

# Check if Node.js/npm is available for frontend tests
$runFrontendTests = $false
try {
    $nodeVersion = node --version 2>&1
    $npmVersion = npm --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Node.js $nodeVersion and npm $npmVersion found. Frontend tests will run." -ForegroundColor Green
        $runFrontendTests = $true
    } else {
        Write-Host "WARNING: Node.js/npm not found. Frontend tests will be skipped." -ForegroundColor Yellow
    }
} catch {
    Write-Host "WARNING: Node.js/npm not found. Frontend tests will be skipped." -ForegroundColor Yellow
}

# Run pytest
Write-Host "`nExecuting tests..." -ForegroundColor Cyan
if ($useCoverage) {
    # Run with coverage and generate detailed report
    python -m pytest backend\tests\ -v --cov=backend\src --cov-report=term-missing --cov-report=html:htmlcov
    Write-Host "`nCoverage report generated in htmlcov/index.html" -ForegroundColor Cyan
} else {
    # Run without coverage
    python -m pytest backend\tests\ -v
}

# Show test file summary
Write-Host "`n=== Test Files Summary ===" -ForegroundColor Cyan
$testFiles = (Get-ChildItem -Path "backend\tests" -Recurse -Filter "test_*.py" | Measure-Object).Count
Write-Host "   Test files: $testFiles" -ForegroundColor Green
$unitTests = (Get-ChildItem -Path "backend\tests\unit" -Filter "test_*.py" | Measure-Object).Count
$integrationTests = (Get-ChildItem -Path "backend\tests\integration" -Filter "test_*.py" | Measure-Object).Count
Write-Host "   - Unit tests: $unitTests files (includes CLI, schemas, business logic)" -ForegroundColor Green
Write-Host "   - Integration tests: $integrationTests files (includes API, database, storage)" -ForegroundColor Green

$backendTestsPassed = $LASTEXITCODE -eq 0

# Frontend Testing (Phase 5.1/5.2)
Write-Host "`n=== Frontend Testing (Phase 5.1/5.2) ===" -ForegroundColor Cyan

# Initialize frontend test result
$frontendTestsPassed = $true

if ($runFrontendTests) {
    # Check if frontend directory exists
    if (Test-Path "frontend") {
        Push-Location frontend
        
        # Phase 5.1: Frontend Setup Tests
        Write-Host "`nPhase 5.1: Frontend Setup" -ForegroundColor Cyan
        
        # Check package.json exists
        if (Test-Path "package.json") {
            Write-Host "   package.json: Found" -ForegroundColor Green
        } else {
            Write-Host "   package.json: NOT FOUND" -ForegroundColor Red
            $frontendTestsPassed = $false
            Pop-Location
            $frontendTestsPassed = $false
            $runFrontendTests = $false
        }
        
        # Check vite.config.ts exists
        if (Test-Path "vite.config.ts") {
            Write-Host "   vite.config.ts: Found" -ForegroundColor Green
        } else {
            Write-Host "   vite.config.ts: NOT FOUND" -ForegroundColor Red
            $frontendTestsPassed = $false
        }
        
        # Check tsconfig.json exists
        if (Test-Path "tsconfig.json") {
            Write-Host "   tsconfig.json: Found" -ForegroundColor Green
        } else {
            Write-Host "   tsconfig.json: NOT FOUND" -ForegroundColor Red
            $frontendTestsPassed = $false
        }
        
        # Check if node_modules exists (dependencies installed)
        if (-not (Test-Path "node_modules")) {
            Write-Host "   WARNING: Frontend dependencies not installed." -ForegroundColor Yellow
            Write-Host "   Run: cd frontend && npm install" -ForegroundColor Yellow
            Write-Host "   Skipping compilation and linting tests." -ForegroundColor Yellow
        } else {
            Write-Host "   node_modules: Found" -ForegroundColor Green
            
            # TypeScript compilation test
            Write-Host "`n   Running TypeScript compilation..." -ForegroundColor Cyan
            $buildOutput = npm run build 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   TypeScript compilation: PASSED" -ForegroundColor Green
                
                # Verify build output exists
                if (Test-Path "dist") {
                    Write-Host "   Build output (dist/): PASSED" -ForegroundColor Green
                } else {
                    Write-Host "   Build output (dist/): FAILED" -ForegroundColor Red
                    $frontendTestsPassed = $false
                }
            } else {
                Write-Host "   TypeScript compilation: FAILED" -ForegroundColor Red
                Write-Host "   Build errors:" -ForegroundColor Yellow
                $buildOutput | Select-String -Pattern "error TS" | ForEach-Object {
                    Write-Host "     $_" -ForegroundColor Yellow
                }
                Write-Host "   Run 'npm run build' in frontend/ for full details" -ForegroundColor Yellow
                $frontendTestsPassed = $false
            }
        }
        
        # Phase 5.2: API Client Service Tests
        Write-Host "`nPhase 5.2: API Client Service" -ForegroundColor Cyan
        
        $apiClientPath = "src\services\api.ts"
        if (Test-Path $apiClientPath) {
            Write-Host "   API client file (src/services/api.ts): Found" -ForegroundColor Green
            
            # Verify API client structure
            $apiContent = Get-Content $apiClientPath -Raw
            $checks = @{
                "api object export" = $apiContent -match "export const api ="
                "handleApiError function" = $apiContent -match "export function handleApiError"
                "healthCheck function" = $apiContent -match "export const healthCheck"
                "axios import" = $apiContent -match "import.*axios"
                "devices endpoints" = $apiContent -match "devices:\s*\{"
                "testStages endpoints" = $apiContent -match "testStages:\s*\{"
                "requirementSets endpoints" = $apiContent -match "requirementSets:\s*\{"
                "testRuns endpoints" = $apiContent -match "testRuns:\s*\{"
            }
            
            $allChecksPassed = $true
            foreach ($check in $checks.GetEnumerator()) {
                if ($check.Value) {
                    Write-Host "   - $($check.Key): PASSED" -ForegroundColor Green
                } else {
                    Write-Host "   - $($check.Key): FAILED" -ForegroundColor Red
                    $allChecksPassed = $false
                }
            }
            
            if ($allChecksPassed) {
                Write-Host "   API client structure: VALID" -ForegroundColor Green
            } else {
                Write-Host "   API client structure: INVALID (missing expected exports)" -ForegroundColor Red
                $frontendTestsPassed = $false
            }
        } else {
            Write-Host "   API client file (src/services/api.ts): NOT FOUND" -ForegroundColor Red
            $frontendTestsPassed = $false
        }
        
        # Optional: Run linting (non-blocking)
        if (Test-Path "node_modules") {
            Write-Host "`n   Running ESLint (non-blocking)..." -ForegroundColor Cyan
            $lintOutput = npm run lint 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ESLint: PASSED" -ForegroundColor Green
            } else {
                Write-Host "   ESLint: WARNINGS (non-blocking)" -ForegroundColor Yellow
                $lintOutput | Select-String -Pattern "warning|error" | Select-Object -First 5 | ForEach-Object {
                    Write-Host "     $_" -ForegroundColor Yellow
                }
                Write-Host "   Run 'npm run lint' in frontend/ for full details" -ForegroundColor Yellow
            }
        }
        
        Pop-Location
        
        if (-not $frontendTestsPassed) {
            Write-Host "`n   Frontend tests failed. Check output above for details." -ForegroundColor Red
        }
    } else {
        Write-Host "Frontend directory not found. Skipping frontend tests." -ForegroundColor Yellow
        $frontendTestsPassed = $true  # Don't fail if frontend doesn't exist
    }
} else {
    Write-Host "Node.js/npm not available. Skipping frontend tests." -ForegroundColor Yellow
    Write-Host "Install Node.js to test frontend: https://nodejs.org/" -ForegroundColor Yellow
    $frontendTestsPassed = $true  # Don't fail if Node.js isn't available
}

# Final Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
if ($backendTestsPassed) {
    Write-Host "   Backend tests: PASSED" -ForegroundColor Green
} else {
    Write-Host "   Backend tests: FAILED" -ForegroundColor Red
}

if ($frontendTestsPassed) {
    Write-Host "   Frontend tests: PASSED" -ForegroundColor Green
} else {
    Write-Host "   Frontend tests: FAILED" -ForegroundColor Red
}

if ($backendTestsPassed -and $frontendTestsPassed) {
    Write-Host "`nAll tests completed successfully!" -ForegroundColor Green
    
    if ($useCoverage) {
        Write-Host "`nCoverage Report:" -ForegroundColor Cyan
        Write-Host "   - HTML report: htmlcov\index.html" -ForegroundColor Yellow
        Write-Host "   - JSON report: coverage.json" -ForegroundColor Yellow
        Write-Host "`nTip: Open htmlcov\index.html in your browser for detailed coverage analysis" -ForegroundColor Cyan
    }
} else {
    Write-Host "`nSome tests failed!" -ForegroundColor Red
    if (-not $backendTestsPassed) {
        exit 1
    }
    if (-not $frontendTestsPassed) {
        exit 1
    }
}

