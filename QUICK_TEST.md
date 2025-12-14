# Quick Test Guide

This guide provides minimal "does it work" checks for the RF Performance Tool.

## Running Tests

### Windows

**Option 1: Use the PowerShell script (Recommended)**
```powershell
.\test_all.ps1
```

**Option 2: Use the batch file (Command Prompt)**
```cmd
test_all.bat
```

**Option 3: Run pytest directly**
```powershell
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Run tests
python -m pytest backend\tests\ -v --cov=backend\src
```

**Option 4: Run specific test files**
```powershell
python -m pytest backend\tests\unit\test_metadata.py -v
python -m pytest backend\tests\unit\test_device.py -v
```

### macOS / Linux

**Option 1: Use the shell script**
```bash
./test_all.sh
```

**Option 2: Run pytest directly**
```bash
# Activate virtual environment first
source .venv/bin/activate

# Run tests
python3 -m pytest backend/tests/ -v --cov=backend/src
```

## Minimal Test Check

To verify the basic setup works, run just the schema validation tests:

```bash
# Windows
python -m pytest backend\tests\unit\test_metadata.py backend\tests\unit\test_device.py -v

# macOS/Linux
python3 -m pytest backend/tests/unit/test_metadata.py backend/tests/unit/test_device.py -v
```

This should run quickly and verify that:
- Pydantic models are working
- Validation logic is correct
- Test infrastructure is set up properly

## Expected Output

When tests pass, you should see:
- Test names with [PASSED] status
- Coverage report showing which lines are covered
- Summary at the end showing number of tests passed

## Troubleshooting

### "pytest not found"
Make sure you've:
1. Created and activated the virtual environment
2. Installed dependencies: `pip install -r backend/requirements.txt`

### "Module not found: backend.src"
Make sure you're running pytest from the repository root directory, not from inside the backend/ directory.

### "Python version error"
Ensure you're using Python 3.10+ (3.11 or 3.12 recommended).

