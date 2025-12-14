# RF Test & Analysis Tool - Testability-Focused Phased Implementation Plan

**⚠️ LOCKED FILE - DO NOT MODIFY ⚠️**

This plan is locked and should not be overwritten or modified. It serves as the authoritative testability-focused implementation guide.

For reference, see also: `rf_test_analysis_tool_implementation_LOCKED.plan.md` (original specification)

---

**Principle: Testing ability is the highest priority. Every business logic component must be testable independently, with comprehensive test coverage, before any UI integration.**

**Core Boundary Rule**: Core business logic modules must not import FastAPI, SQLAlchemy, or filesystem paths; all such interactions occur through injected interfaces.

## Testability Principles

1. **Test-First Development**: Write tests before or alongside implementation
2. **Independent Testability**: Business logic is filesystem-independent except at explicit boundaries (loader reads files, plotting writes PNGs - these are boundary components)
3. **CLI Access**: All computations must be accessible via CLI for testing and debugging
4. **Mockable Interfaces**: Dependencies (storage, file I/O) must be abstracted and mockable
5. **Comprehensive Fixtures**: Rich test data fixtures created early
6. **Deterministic Tests**: All tests must be deterministic and repeatable
7. **Fast Test Execution**: Unit tests < 10 seconds, full test suite < 60 seconds

## Phase 0: Test Infrastructure & Core Schemas (Foundation for Testing)

**Goal**: Establish test infrastructure and data models that enable all future testing.

### 0.1 Repository Structure & Test Setup

- Create directory structure (backend/, frontend/, docs/, results/)
- **Python version**: Python 3.11 or 3.12 recommended, >=3.10 required (not 3.14+ due to dependency compatibility)
- Standardize venv location: `.venv` at repo root
- Create `backend/requirements.txt` with:
  - FastAPI, Pydantic, SQLAlchemy
  - scikit-rf, matplotlib, numpy
  - **pytest, pytest-cov, pytest-mock, pytest-asyncio** (testing dependencies)
  - **hypothesis** (property-based testing)
- Create `backend/pytest.ini` with test configuration
- Create `backend/tests/` structure:
  - `tests/unit/` - Pure unit tests (no I/O)
  - `tests/integration/` - Integration tests (with database/filesystem)
  - `tests/fixtures/` - Test data fixtures
  - `tests/conftest.py` - Shared pytest fixtures
- Create `test_all.sh` script that runs:
  - `pytest backend/tests/` with coverage
  - Frontend typecheck (optional)

**Package Structure (Boundary Enforcement):**
- `backend/src/core/` - Pure business logic (must not import api, storage, or FastAPI)
- `backend/src/api/` - FastAPI app and routes
- `backend/src/storage/` - SQLite and filesystem operations
- `backend/src/plugins/` - Test type plugins (s_parameter/)
- `backend/src/services/` - Service layer (orchestration, uses core + storage interfaces)
- `backend/src/cli/` - CLI tool entry point

### 0.2 Core Schemas (Pydantic Models) - Testable First

**Create in `backend/src/core/schemas/` with comprehensive validation tests:**

- `device.py`: Device, DeviceConfig, SParameterConfig
  - **SParameterConfig must include:**
    - `gain_parameter`: default "S21" (string, validated against port count)
    - `input_return_parameter`: default "S11" (validated against port count)
    - `output_return_parameter`: default "S22" (optional, validated against port count)
    - Schema validation: Reject invalid Sij (e.g., "S91" on 4-port device, "S21" on 1-port)
  - **Test**: Validation of frequency bands, parameter names (S21, S31, etc.)
  - **Test**: Sij parameter validation against port count
  - **Test**: Default values and required fields
- `test_stage.py`: TestStage
  - **Test**: Name validation, format constraints (uniqueness is storage-level, tested in Phase 2)
- `requirement_set.py`: RequirementSet, MetricLimit, FrequencyBand, PassPolicy
  - **MetricLimit must include:**
    - `aggregation`: enum {min, max, avg, pkpk} (peak-to-peak)
    - `operator`: enum {<=, >=, <, >} or `limit_type` per metric
    - `frequency_band`: FrequencyBand (slice data by band first, then aggregate)
  - **Test**: Metric limit validation, frequency band validation
  - **Test**: Aggregation semantics (slice by band, then aggregate)
  - **Test**: Pass policy logic
- `test_run.py`: TestRun, TestRunStatus, TestRunFile
  - **Test**: Immutability constraints, status transitions
- `plotting.py`: PlotSpec, PlotConfig, PlotSeries
  - **Test**: PlotSpec validation, PlotConfig defaults
- `metadata.py`: ParsedMetadata, EffectiveMetadata
  - **Test**: Metadata merge logic (parsed + overrides = effective)

**Each schema file must have corresponding `tests/unit/test_<schema>.py` with validation tests.**

### 0.3 Test Fixtures & Sample Data

**Create comprehensive test fixtures in `backend/tests/fixtures/`:**

- `sample_s2p/` - Sample S2P files (various formats, edge cases)
- `sample_s3p/` - Sample S3P files
- `sample_s4p/` - Sample S4P files
- `sample_filenames.txt` - Test cases for filename parsing:
  - `SN1234_PRI_L567890_AMB_20240101.s2p`
  - `RED_sn0001_l123456_cld_240101.s2p`
  - `L999999_HOT_20231231_PRI_SN9999.s3p`
  - Edge cases: missing tokens, unknown tokens, case variations
- `sample_devices.json` - Device configurations for testing
- `sample_requirement_sets.json` - Requirement sets for testing

**Create pytest fixtures in `tests/conftest.py`:**

- `sample_s2p_file` - Returns path to sample S2P
- `sample_s3p_file` - Returns path to sample S3P
- `sample_s4p_file` - Returns path to sample S4P
- `sample_device_config` - Returns DeviceConfig for testing
- `sample_requirement_set` - Returns RequirementSet for testing
- `in_memory_db` - SQLite in-memory database for testing
- `temp_results_dir` - Temporary directory for artifact testing

## Phase 1: Testable Business Logic (No API, No UI)

**Goal**: Implement all business logic with comprehensive tests, accessible via CLI. No FastAPI routes yet.

### 1.1 Storage Abstractions (Testable Interfaces)

**Create abstract interfaces in `backend/src/storage/interfaces.py`:**

- `IDatabase` - Abstract database operations
- `IFileStorage` - Abstract file storage operations
- `IStorageFactory` - Factory for creating storage instances

**Implementations:**

- `backend/src/storage/sqlite_db.py` - SQLite implementation
- `backend/src/storage/file_storage.py` - Filesystem implementation
- **Note**: `mock_storage.py` is useful but don't overbuild it; pytest fixtures + temp dirs + sqlite :memory: cover most needs

**Tests:**

- `tests/unit/test_storage_interfaces.py` - Test interfaces with mocks
- `tests/integration/test_storage_impl.py` - Test real implementations

### 1.2 Filename Parser (Pure Function, Highly Testable)

**Implement `backend/src/plugins/s_parameter/parser.py`:**

- Pure function: `parse_filename_metadata(filename: str) -> ParsedMetadata`
- Token extraction logic (SN, PRI/RED, Lxxxxxx, CLD/AMB/HOT, dates)
- Case-insensitive, order-independent parsing
- Missing token reporting
- Unknown token ignoring

**Tests in `tests/unit/test_filename_parser.py`:**

- Test all token types individually
- Test token order independence
- Test case insensitivity
- Test missing tokens (should report, not fail)
- Test unknown tokens (should ignore)
- Test date normalization (YYYYMMDD, YYMMDD -> ISO)
- Test edge cases: empty filename, special characters, multiple matches
- **Use hypothesis for property-based testing of parsing rules**

**CLI command**: `rf-tool parse <filename>` (for manual testing)

### 1.3 S-Parameter File Loader (Testable with Fixtures - Boundary Component)

**Implement `backend/src/plugins/s_parameter/loader.py`:**

- Function: `load_s_parameter_file(file_path: str) -> Network` (scikit-rf Network)
- Support S2P, S3P, S4P
- Error handling for invalid files
- **Note**: This is a boundary component (reads filesystem) - testable using temp dirs and fixture files

**Tests in `tests/unit/test_s_parameter_loader.py`:**

- Test loading S2P files (using fixtures)
- Test loading S3P files (using fixtures)
- Test loading S4P files (using fixtures)
- Test error handling for invalid files
- Test file format variations
- **Use temporary directories and fixture files for all tests**

**CLI command**: `rf-tool load <file_path>` (prints network info)

### 1.4 Metrics Computation (Pure Functions, Highly Testable)

**Implement `backend/src/plugins/s_parameter/metrics.py`:**

- Pure functions (no side effects):
- `compute_gain_db(network: Network, sij_param: str) -> ndarray`
- `compute_vswr(network: Network, sii_param: str) -> ndarray`
- `compute_return_loss_db(network: Network, sii_param: str) -> ndarray`
- `compute_gain_flatness(gain_db: ndarray, frequencies: ndarray, band: FrequencyBand) -> float`
- All functions take Network and parameters, return computed values
- No database or file I/O

**Tests in `tests/unit/test_metrics_computation.py`:**

- Test gain computation with known S-parameter values (verify formula: 20*log10(|Sxy|))
- Test VSWR computation (verify formula: (1+|Γ|)/(1-|Γ|))
- Test return loss computation (verify formula: -20*log10(|Sii|))
- Test gain flatness over frequency bands
- Test with different Sij parameters (S21, S31, S11, S22, etc.)
- Test edge cases: zero values, negative values, out-of-band frequencies
- **Use known test vectors** (e.g., S21=0.5 -> Gain ≈ -6.02 dB)
- **Golden file regression test**: Fixed S2P/S3P/S4P fixture with expected computed outputs in JSON snapshot; test compares computed result within tolerance (catches accidental refactors)

**CLI command**: `rf-tool compute <file_path> <device_config_json>` (prints computed metrics)

### 1.5 Compliance Evaluation (Pure Logic, Highly Testable)

**Implement `backend/src/plugins/s_parameter/compliance.py`:**

- Pure function: `evaluate_compliance(metrics: dict, requirement_set: RequirementSet) -> ComplianceResult`
- Pass/fail determination per requirement, per file
- Failure reason generation
- Respect pass policy (`all_files_must_pass`, `required_paths`)

**Tests in `tests/unit/test_compliance_evaluation.py`:**

- Test pass/fail determination for each metric type
- Test requirement aggregation rules (min, max, avg, pkpk)
- Test aggregation with frequency band slicing (slice by band first, then aggregate)
- Test evaluation operators (<=, >=, <, >)
- Test pass policy logic (`all_files_must_pass=True` vs `False`)
- Test failure reason generation
- Test edge cases: exactly at limit, slightly over, multiple failures
- Test with various requirement set configurations

**CLI command**: `rf-tool evaluate <metrics_json> <requirements_json>` (prints compliance results)

### 1.6 Plotting System (Testable Rendering - Boundary Component)

**Implement `backend/src/plugins/s_parameter/plotting.py`:**

- `PlotSpec` and `PlotConfig` models (already in schemas)
- Function: `render_plot(plot_spec: PlotSpec, plot_config: PlotConfig, output_path: str) -> str`
- Uses matplotlib, writes PNG to filesystem
- Returns path to generated file
- **Note**: This is a boundary component (writes filesystem) - testable using temp dirs

**Tests in `tests/unit/test_plotting.py`:**

- Test PlotSpec validation
- Test PlotConfig defaults and overrides
- Test plot rendering with known data
- Test metadata subtitle generation
- Test PRI vs RED line styling
- Test axis limits application
- **Deterministic plotting tests** (tolerance-based, not pixel-perfect):
  - File exists
  - File size > N bytes (reasonable minimum)
  - Image dimensions match expected (from PlotConfig)
  - Validate PlotSpec/PlotConfig serialization
  - **Do not pixel-compare** (platform-dependent)

**CLI command**: `rf-tool plot <spec_json> <config_json> <output.png>` (generates plot)

### 1.7 Service Layer (Orchestration, Testable with Mocks)

**Implement `backend/src/services/test_run_service.py`:**

- Orchestrates: parse -> load -> compute -> evaluate -> plot
- Takes storage interfaces (dependency injection)
- Pure business logic, no FastAPI dependencies

**Tests in `tests/unit/test_test_run_service.py`:**

- Test full pipeline with mocked storage
- Test error handling at each step
- Test immutability enforcement
- Test requirement hash computation
- **Use mocks for all I/O operations**

**CLI command**: `rf-tool run <test_run_id> <file_paths...>` (runs full pipeline)

## Phase 2: Persistence Integration

**Goal**: Implement persistence layer with comprehensive integration tests.

### 2.1 Database Models & Migrations

**Implement `backend/src/storage/models.py`:**

- SQLAlchemy models for all tables
- Database initialization
- Migration utilities

**Tests in `tests/integration/test_database.py`:**

- Test table creation
- Test CRUD operations for each model
- Test immutability constraints (TestRun updates should fail)
- Test foreign key relationships
- Test requirement hash storage
- Test uniqueness constraints (e.g., TestStage names)
- **Use in-memory SQLite for fast tests**

### 2.2 File Storage Implementation

**Implement `backend/src/storage/file_storage.py`:**

- File upload handling
- Artifact path management
- Directory structure creation

**Tests in `tests/integration/test_file_storage.py`:**

- Test file upload and storage
- Test artifact directory creation
- Test path resolution
- Test cleanup (optional)
- **Use temporary directories for tests**

### 2.3 Storage Service Integration

**Implement `backend/src/storage/storage_service.py`:**

- Combines database and file storage
- Implements storage interfaces from Phase 1
- Transaction management

**Tests in `tests/integration/test_storage_service.py`:**

- Test full storage operations
- Test transaction rollback on errors
- Test concurrent access (if applicable)

## Phase 3: Thin API Wrapper

**Goal**: Add FastAPI routes that delegate to tested business logic.

### 3.1 API Routes (Thin Controllers)

**Implement `backend/src/api/routes/`:**

- Device routes: `GET/POST/PUT/DELETE /api/devices`
- Test stage routes: `GET/POST/PUT/DELETE /api/test-stages`
- Requirement set routes: `GET/POST/PUT/DELETE /api/requirement-sets`
- Test run routes: `POST /api/test-runs`, `GET /api/test-runs`, `GET /api/test-runs/{id}`
- Upload route: `POST /api/test-runs/{id}/upload`
- Compliance route: `GET /api/test-runs/{id}/compliance`
- Plot routes: `GET /api/test-runs/{id}/plots/{plot_type}`, `GET /api/test-runs/{id}/plot-data/{plot_type}`

**Each route:**

- Validates request with Pydantic models
- Calls service layer (already tested)
- Returns response
- Handles errors

**Tests in `tests/integration/test_api_routes.py`:**

- Use FastAPI TestClient
- Test each endpoint with valid/invalid inputs
- Test error responses
- Test authentication (none required, but test that it's not required)
- **Mock service layer if needed, but prefer real service with test database**

### 3.2 FastAPI App Setup

**Implement `backend/src/main.py`:**

- FastAPI app creation
- Route registration
- CORS configuration (dev vs prod)
- Static file serving (prod mode)
- Health check endpoint

**Tests:**

- Test health check endpoint
- Test CORS headers in dev mode
- Test static file serving in prod mode

## Phase 4: CLI Tool (Full-Featured Testing Interface)

**Goal**: Create comprehensive CLI tool for testing all functionality without UI.

### 4.1 CLI Implementation

**Implement `backend/src/cli/main.py`:**

- Install backend as a package (e.g., `rf_tool`) to avoid PATH/version confusion
- Entry point: `rf-tool` command (via `pyproject.toml` entry_points or setup.py)
- Command structure:
  - `rf-tool parse <filename>` - Test filename parsing
  - `rf-tool load <file_path>` - Test S-parameter loading
  - `rf-tool compute <file_path> <device_config_json>` - Compute metrics
  - `rf-tool evaluate <metrics_json> <requirements_json>` - Evaluate compliance
  - `rf-tool plot <spec_json> <config_json> <output.png>` - Generate plot
  - `rf-tool run <test_run_id> <file_paths...>` - Run full pipeline
  - `rf-tool test-db` - Test database operations
  - `rf-tool test-storage` - Test file storage

**Each command:**

- Uses tested business logic
- Provides clear output
- Handles errors gracefully
- Useful for debugging and manual testing

**Package structure**: Use `python -m rf_tool.cli ...` or install as `rf-tool` command (not `python -m backend.src...`)

## Phase 5: Frontend (UI Layer, Minimal Business Logic)

**Goal**: Build UI that displays backend-computed results. No business logic in frontend.

### 5.1 Frontend Setup

- Vite + React + TypeScript
- API client service (axios)
- Type generation from OpenAPI schema

### 5.2 UI Components

- Device management UI (calls API)
- Test stage management UI (calls API)
- Requirement set editor UI (calls API)
- Test run list/detail UI (calls API)
- File upload UI (calls API)
- Compliance table display (displays backend data)
- Plot viewer (displays backend PNGs, uses backend series data for interactive plots)

**Frontend tests (optional, lower priority):**

- Component rendering tests
- API client tests (mocked)
- No business logic tests (all in backend)

## Phase 6: Integration & End-to-End Testing

**Goal**: Verify full system works together.

### 6.1 End-to-End Tests

**Create `tests/e2e/test_full_pipeline.py`:**

- Test: Create device -> Create requirement set -> Create test run -> Upload file -> Verify results
- Test: Full S-parameter analysis pipeline
- Test: Plot generation and retrieval
- Test: Compliance evaluation
- **Use test database and temporary file storage**

### 6.2 System Tests

- Test startup scripts
- Test DEV mode (backend + vite)
- Test PROD mode (backend serves static)
- Test port conflict handling
- Test error messages

## Testing Coverage Goals

- **Unit tests**: 90%+ coverage of business logic (parser, metrics, compliance, plotting)
- **Integration tests**: 80%+ coverage of storage and API layers
- **Test runtime budget**:
  - Unit tests: < 10 seconds
  - Full test suite: < 60 seconds (accounts for matplotlib + scikit-rf overhead)
- **All tests**: Must be deterministic (no flaky tests)
- **Golden file regression**: Fixed S2P/S3P/S4P fixtures with expected outputs in JSON snapshots

## Implementation Order Summary

1. **Phase 0**: Test infrastructure, schemas, fixtures
2. **Phase 1**: All business logic (parser, loader, metrics, compliance, plotting) - **TESTED**
   - Boundary components (loader, plotting) use temp dirs and fixtures
3. **Phase 2**: Persistence integration - **TESTED**
4. **Phase 3**: Thin API wrapper - **TESTED**
5. **Phase 4**: CLI tool (for testing/debugging)
6. **Phase 5**: Frontend (display only)
7. **Phase 6**: End-to-end integration

**Key Rule**: Never implement a feature without tests. Tests are written first or alongside implementation, never after.

**Package Boundary Enforcement**: Core business logic modules (`backend/src/core/`) must not import FastAPI, SQLAlchemy, or filesystem paths; all such interactions occur through injected interfaces.

---

**⚠️ END OF LOCKED PLAN ⚠️**

This document is locked and should not be modified. It represents the authoritative testability-focused implementation strategy.

