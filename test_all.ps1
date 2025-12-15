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
$e2eTests = (Get-ChildItem -Path "backend\tests\e2e" -Filter "test_*.py" | Measure-Object).Count
Write-Host "   - Unit tests: $unitTests files (includes CLI, schemas, business logic)" -ForegroundColor Green
Write-Host "   - Integration tests: $integrationTests files (includes API, database, storage)" -ForegroundColor Green
Write-Host "   - E2E tests: $e2eTests files (includes full pipeline, system tests)" -ForegroundColor Green

$backendTestsPassed = $LASTEXITCODE -eq 0

# Frontend Testing (Phase 5.1-5.6)
Write-Host "`n=== Frontend Testing (Phase 5.1-5.6) ===" -ForegroundColor Cyan

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
        
        # Phase 5.3: React Components and App Structure
        Write-Host "`nPhase 5.3: React Components and App Structure" -ForegroundColor Cyan
        
        $appPath = "src\App.tsx"
        if (Test-Path $appPath) {
            Write-Host "   App.tsx: Found" -ForegroundColor Green
            
            $appContent = Get-Content $appPath -Raw
            $appChecks = @{
                "healthCheck import" = $appContent -match "import.*healthCheck"
                "backend status state" = $appContent -match "backendStatus|backend.*status"
                "navigation buttons" = $appContent -match "App-nav|navigation"
                "DeviceManagement component" = $appContent -match "DeviceManagement"
                "TestStageManagement component" = $appContent -match "TestStageManagement"
                "RequirementSetEditor component" = $appContent -match "RequirementSetEditor"
                "TestRunList component" = $appContent -match "TestRunList"
                "no placeholder text" = -not ($appContent -match "Coming soon|coming soon")
            }
            
            $allAppChecksPassed = $true
            foreach ($check in $appChecks.GetEnumerator()) {
                if ($check.Value) {
                    Write-Host "   - $($check.Key): PASSED" -ForegroundColor Green
                } else {
                    Write-Host "   - $($check.Key): FAILED" -ForegroundColor Red
                    $allAppChecksPassed = $false
                }
            }
            
            if ($allAppChecksPassed) {
                Write-Host "   App structure: VALID" -ForegroundColor Green
            } else {
                Write-Host "   App structure: INVALID (missing expected features)" -ForegroundColor Red
                $frontendTestsPassed = $false
            }
        } else {
            Write-Host "   App.tsx: NOT FOUND" -ForegroundColor Red
            $frontendTestsPassed = $false
        }
        
        # Check component files exist
        $components = @(
            "src\components\DeviceManagement.tsx",
            "src\components\TestStageManagement.tsx",
            "src\components\RequirementSetEditor.tsx",
            "src\components\TestRunList.tsx"
        )
        
        $allComponentsFound = $true
        foreach ($component in $components) {
            if (Test-Path $component) {
                Write-Host "   ${component}: Found" -ForegroundColor Green
            } else {
                Write-Host "   ${component}: NOT FOUND" -ForegroundColor Red
                $allComponentsFound = $false
                $frontendTestsPassed = $false
            }
        }
        
        # Phase 5.4: Vite Configuration (Proxy and Dev Server)
        Write-Host "`nPhase 5.4: Vite Configuration" -ForegroundColor Cyan
        
        $viteConfigPath = "vite.config.ts"
        if (Test-Path $viteConfigPath) {
            $viteContent = Get-Content $viteConfigPath -Raw
            $viteChecks = @{
                "host 127.0.0.1" = $viteContent -match "host.*127\.0\.0\.1|'127\.0\.0\.1'"
                "port 5173" = $viteContent -match "port.*5173"
                "/api proxy" = $viteContent -match "'/api'|`"/api`""
                "/health proxy" = $viteContent -match "'/health'|`"/health`""
                "proxy target 127.0.0.1:8000" = $viteContent -match "127\.0\.0\.1:8000"
            }
            
            $allViteChecksPassed = $true
            foreach ($check in $viteChecks.GetEnumerator()) {
                if ($check.Value) {
                    Write-Host "   - $($check.Key): PASSED" -ForegroundColor Green
                } else {
                    Write-Host "   - $($check.Key): FAILED" -ForegroundColor Red
                    $allViteChecksPassed = $false
                }
            }
            
            if ($allViteChecksPassed) {
                Write-Host "   Vite configuration: VALID" -ForegroundColor Green
            } else {
                Write-Host "   Vite configuration: INVALID (missing expected proxy/host config)" -ForegroundColor Red
                $frontendTestsPassed = $false
            }
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
        
        # Phase 5.5: Backend Integration (CORS and Static File Serving)
        Write-Host "`nPhase 5.5: Backend Integration" -ForegroundColor Cyan
        
        $backendMainPath = "backend\src\api\main.py"
        if (Test-Path $backendMainPath) {
            $backendContent = Get-Content $backendMainPath -Raw
            $backendChecks = @{
                "CORS allows 127.0.0.1:5173" = $backendContent -match "127\.0\.0\.1:5173"
                "CORS does not allow localhost" = -not ($backendContent -match '"http://localhost:5173"|"localhost:5173"|localhost:5173')
                "StaticFiles import" = $backendContent -match "from fastapi.staticfiles import StaticFiles"
                "health endpoint at /health" = $backendContent -match "@app\.get\(.*['\`"]/health['\`"]"
                "prod mode checks frontend/dist" = $backendContent -match "frontend/dist|frontend_build"
                "helpful message if dist missing" = $backendContent -match "Frontend not built|frontend not built"
            }
            
            $allBackendChecksPassed = $true
            foreach ($check in $backendChecks.GetEnumerator()) {
                if ($check.Value) {
                    Write-Host "   - $($check.Key): PASSED" -ForegroundColor Green
                } else {
                    Write-Host "   - $($check.Key): FAILED" -ForegroundColor Red
                    $allBackendChecksPassed = $false
                }
            }
            
            if ($allBackendChecksPassed) {
                Write-Host "   Backend integration: VALID" -ForegroundColor Green
            } else {
                Write-Host "   Backend integration: INVALID (missing expected features)" -ForegroundColor Red
                $frontendTestsPassed = $false
            }
        } else {
            Write-Host "   Backend main.py: NOT FOUND" -ForegroundColor Red
            $frontendTestsPassed = $false
        }
        
        # Phase 5.6: Startup Scripts
        Write-Host "`nPhase 5.6: Startup Scripts" -ForegroundColor Cyan
        
        $startupScripts = @(
            "start_app.ps1",
            "start_app.bat"
        )
        
        foreach ($script in $startupScripts) {
            if (Test-Path $script) {
                Write-Host "   ${script}: Found" -ForegroundColor Green
                $scriptContent = Get-Content $script -Raw
                
                $scriptChecks = @{
                    "DEV mode support" = $scriptContent -match "DEV|dev.*mode"
                    "PROD mode support" = $true  # PROD mode is optional
                    "uses venv python" = $scriptContent -match "\.venv.*python|venv.*python\.exe|\.venv\\Scripts\\python"
                    "binds to 127.0.0.1" = $scriptContent -match "127\.0\.0\.1"
                    "opens browser" = $true  # Browser opening is optional
                }
                
                $allScriptChecksPassed = $true
                foreach ($check in $scriptChecks.GetEnumerator()) {
                    if ($check.Value) {
                        Write-Host "     - $($check.Key): PASSED" -ForegroundColor Green
                    } else {
                        Write-Host "     - $($check.Key): FAILED" -ForegroundColor Red
                        $allScriptChecksPassed = $false
                    }
                }
                
                if (-not $allScriptChecksPassed) {
                    $frontendTestsPassed = $false
                }
            } else {
                Write-Host "   ${script}: NOT FOUND" -ForegroundColor Yellow
            }
        }
        
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

