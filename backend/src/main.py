"""
Main entry point for running the FastAPI server.
"""
import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("RF_TOOL_HOST", "127.0.0.1")
    port = int(os.getenv("RF_TOOL_PORT", "8000"))
    dev_mode = os.getenv("RF_TOOL_DEV_MODE", "true").lower() == "true"
    reload = dev_mode  # Auto-reload in dev mode
    
    # Import app
    from backend.src.api.main import create_app
    app = create_app(dev_mode=dev_mode)
    
    # Run server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


