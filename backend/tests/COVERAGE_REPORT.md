# Test Coverage Report

This document shows the current test coverage status for all files in the backend.

## Overall Coverage: 89%

## Files by Coverage

### 100% Coverage ✅
- `core/schemas/metadata.py` - 100%
- `core/schemas/plotting.py` - 100%
- `core/schemas/requirement_set.py` - 100%
- `core/schemas/test_run.py` - 100%
- `core/schemas/test_stage.py` - 100%
- `plugins/s_parameter/loader.py` - 100%
- `plugins/s_parameter/metrics.py` - 100%
- `storage/database.py` - 100%
- `storage/file_storage.py` - 100%
- `storage/models.py` - 100%
- `storage/storage_service.py` - 100%

### High Coverage (90-99%) ✅
- `plugins/s_parameter/compliance.py` - 96%
- `plugins/s_parameter/parser.py` - 97%
- `plugins/s_parameter/plotting.py` - 98%
- `services/test_run_service.py` - 98%
- `storage/sqlite_db.py` - 99%
- `core/schemas/device.py` - 92%

### Medium Coverage (70-89%) ⚠️
- `storage/interfaces.py` - 70% (abstract methods - expected)
- `storage/mock_storage.py` - 85% (some edge cases)

### Low Coverage (0-69%) ⚠️
- `api/routes/devices.py` - 57% (requires httpx for API tests)
- `api/routes/test_stages.py` - 50% (requires httpx for API tests)
- `api/routes/requirement_sets.py` - 55% (requires httpx for API tests)
- `api/routes/test_runs.py` - 45% (requires httpx for API tests)
- `main.py` - 0% (entry point - hard to test directly)

## Test Files

### Unit Tests
- `test_device.py` - Device schema tests
- `test_metadata.py` - Metadata parsing tests
- `test_plotting.py` - Plotting schema tests
- `test_requirement_set.py` - Requirement set tests
- `test_test_run.py` - Test run schema tests
- `test_test_stage.py` - Test stage schema tests
- `test_filename_parser.py` - Filename parser tests
- `test_s_parameter_loader.py` - S-parameter loader tests
- `test_metrics_computation.py` - Metrics computation tests
- `test_compliance_evaluation.py` - Compliance evaluation tests
- `test_plotting.py` - Plotting system tests
- `test_storage_interfaces.py` - Storage interface tests
- `test_test_run_service.py` - Service layer tests
- `test_phase1_integration.py` - Phase 1 integration tests
- `test_storage_service.py` - Storage service tests
- `test_api_dependencies.py` - API dependency tests
- `test_api_main.py` - API main app tests
- `test_database_utils.py` - Database utility tests
- `test_sqlite_db_helpers.py` - SQLite helper method tests
- `test_device_edge_cases.py` - Device edge case tests
- `test_database_engine_variants.py` - Database engine variant tests

### Integration Tests
- `test_database.py` - Database integration tests (requires SQLAlchemy)
- `test_file_storage.py` - File storage integration tests
- `test_api_routes.py` - API route tests (requires httpx)
- `test_api_comprehensive.py` - Comprehensive API workflow tests (requires httpx)
- `test_api_routes_complete.py` - Complete API endpoint tests (requires httpx)
- `test_storage_service_integration.py` - Storage service integration tests
- `test_sqlite_db_edge_cases.py` - SQLite edge case tests
- `test_sqlite_db_get_methods.py` - SQLite get method tests

## Missing Coverage

### API Routes (45-57%)
**Reason**: API tests require `httpx` package. When installed, coverage increases significantly.
**Action**: Install `httpx` to enable API route tests:
```bash
pip install httpx
```

### main.py (0%)
**Reason**: Entry point script that runs uvicorn server. Difficult to test directly.
**Status**: Acceptable - this is a thin wrapper around uvicorn.

### storage/interfaces.py (70%)
**Reason**: Abstract methods in interfaces. These are tested through implementations.
**Status**: Expected - abstract methods don't need direct testing.

### storage/mock_storage.py (85%)
**Reason**: Some edge cases in mock storage not fully tested.
**Status**: Acceptable - mock storage is primarily for testing other components.

## How to Improve Coverage

1. **Install httpx** to enable API route tests:
   ```bash
   pip install httpx
   ```

2. **Run tests with coverage**:
   ```bash
   python -m pytest backend/tests/ --cov=backend/src --cov-report=html
   ```

3. **View HTML coverage report**:
   Open `htmlcov/index.html` in your browser

## Test Count

- **Total Tests**: 191 (168 passing + 23 skipped)
- **Unit Tests**: ~140
- **Integration Tests**: ~51

## Running All Tests

```powershell
.\test_all.ps1
```

This will:
- Run all tests
- Show coverage report
- Generate HTML coverage report in `htmlcov/index.html`
- Show summary of what's tested


