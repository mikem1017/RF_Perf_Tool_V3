"""
FastAPI application setup.
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.src.api.routes import devices, test_stages, requirement_sets, test_runs


def create_app(dev_mode: bool = True) -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Args:
        dev_mode: If True, enable CORS and dev features. If False, serve static files.
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="RF Performance Tool API",
        description="Local-only RF test analysis application",
        version="1.0.0",
    )
    
    # CORS configuration
    if dev_mode:
        # Dev mode: Allow frontend dev server (127.0.0.1 only, not localhost or 0.0.0.0)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://127.0.0.1:5173",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    # Prod mode: No CORS needed (same origin)
    
    # Register routes
    app.include_router(devices.router)
    app.include_router(test_stages.router)
    app.include_router(requirement_sets.router)
    app.include_router(test_runs.router)
    
    # Health check endpoint
    @app.get("/health")
    def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "version": "1.0.0"}
    
    # Static file serving (prod mode only)
    if not dev_mode:
        frontend_build = Path("frontend/dist")
        if frontend_build.exists() and frontend_build.is_dir():
            # Serve static files from frontend/dist
            app.mount("/", StaticFiles(directory=str(frontend_build), html=True), name="static")
        else:
            # Frontend not built - provide helpful message
            @app.get("/")
            def frontend_not_built():
                return {
                    "error": "Frontend not built",
                    "message": "Frontend build not found. To build the frontend, run: cd frontend && npm install && npm run build",
                    "path": str(frontend_build.absolute())
                }
    
    return app


# Create app instance
# Check environment variable for dev/prod mode
DEV_MODE = os.getenv("RF_TOOL_DEV_MODE", "true").lower() == "true"
app = create_app(dev_mode=DEV_MODE)


