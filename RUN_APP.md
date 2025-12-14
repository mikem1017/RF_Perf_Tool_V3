# Running the RF Performance Tool

This document describes how to run the RF Performance Tool application.

## Prerequisites

1. Python 3.10+ (3.11 or 3.12 recommended)
2. Dependencies installed (see `INSTALL_DEPENDENCIES.md`)
3. Virtual environment activated (recommended)

## Quick Start

### Development Mode (Recommended for Development)

Development mode runs the FastAPI backend and expects a separate frontend dev server.

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run backend server
python -m backend.src.main
```

Or using uvicorn directly:

```bash
uvicorn backend.src.api.main:app --host 127.0.0.1 --port 8000 --reload
```

The server will start at `http://127.0.0.1:8000`

**Features in dev mode:**
- CORS enabled for `http://localhost:5173` and `http://127.0.0.1:5173` (Vite dev server)
- Auto-reload on code changes
- API documentation at `http://127.0.0.1:8000/docs`

### Production Mode

Production mode serves both backend API and frontend static files from a single server.

```bash
# Set environment variable
export RF_TOOL_DEV_MODE=false  # On Windows: set RF_TOOL_DEV_MODE=false

# Run server
python -m backend.src.main
```

**Features in prod mode:**
- No CORS (same origin)
- Static file serving for frontend
- Single server for everything

## Configuration

### Environment Variables

- `RF_TOOL_HOST` - Server host (default: `127.0.0.1`)
- `RF_TOOL_PORT` - Server port (default: `8000`)
- `RF_TOOL_DEV_MODE` - Development mode (default: `true`)
- `RF_TOOL_DATABASE_URL` - Database URL (default: `sqlite:///:memory:` for testing, `sqlite:///rf_tool.db` for production)
- `RF_TOOL_STORAGE_PATH` - File storage base path (default: `results/`)

### Example Configuration

```bash
# Windows PowerShell
$env:RF_TOOL_PORT="8080"
$env:RF_TOOL_DATABASE_URL="sqlite:///rf_tool.db"
python -m backend.src.main

# Linux/macOS
export RF_TOOL_PORT=8080
export RF_TOOL_DATABASE_URL="sqlite:///rf_tool.db"
python -m backend.src.main
```

## API Endpoints

Once the server is running, you can access:

- **API Documentation**: `http://127.0.0.1:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://127.0.0.1:8000/redoc` (ReDoc)
- **Health Check**: `http://127.0.0.1:8000/health`

### Available Routes

- `GET/POST /api/devices` - Device management
- `GET/POST /api/test-stages` - Test stage management
- `GET/POST /api/requirement-sets` - Requirement set management
- `GET/POST /api/test-runs` - Test run management
- `POST /api/test-runs/{id}/upload` - Upload S-parameter files
- `GET /api/test-runs/{id}/compliance` - Get compliance results

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# Use a different port
export RF_TOOL_PORT=8001
python -m backend.src.main
```

### Database Errors

If you see database errors:

1. Ensure SQLAlchemy is installed: `pip install -r backend/requirements.txt`
2. Check database URL: `echo $RF_TOOL_DATABASE_URL`
3. For file-based database, ensure write permissions in the directory

### CORS Errors (Dev Mode)

If you see CORS errors in the browser:

1. Ensure `RF_TOOL_DEV_MODE=true` (default)
2. Check that frontend is running on `http://localhost:5173` or `http://127.0.0.1:5173`
3. Verify CORS middleware is configured in `backend/src/api/main.py`

## Next Steps

- See `INSTALL_DEPENDENCIES.md` for dependency installation
- See `QUICK_TEST.md` for testing instructions
- See `docs/IMPLEMENTATION_PLAN.md` for development roadmap


