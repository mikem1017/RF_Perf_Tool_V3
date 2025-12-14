# Installing Dependencies

This document describes how to install dependencies for the RF Performance Tool.

## Backend Dependencies

### Prerequisites
- Python 3.10+ (3.11 or 3.12 recommended)
- pip (Python package manager)

### Installation Steps

1. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv .venv
   ```

2. **Activate the virtual environment**:
   - On Windows (PowerShell):
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - On Windows (Command Prompt):
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - On macOS/Linux:
     ```bash
     source .venv/bin/activate
     ```

3. **Install backend dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

### Required Packages

The backend requires the following packages (see `backend/requirements.txt`):

- **Web Framework**: FastAPI, uvicorn
- **Data Validation**: Pydantic
- **Database**: SQLAlchemy, Alembic
- **RF Analysis**: scikit-rf
- **Plotting & Math**: matplotlib, numpy
- **Testing**: pytest, pytest-cov, pytest-mock, pytest-asyncio, hypothesis

### Verifying Installation

After installation, verify that dependencies are installed:

```bash
python -c "import fastapi, sqlalchemy, skrf, matplotlib, numpy; print('All dependencies installed!')"
```

### Troubleshooting

- **SQLAlchemy not found**: Make sure you activated the virtual environment and ran `pip install -r backend/requirements.txt`
- **scikit-rf installation issues**: Ensure you have Python 3.10+ and try upgrading pip: `pip install --upgrade pip`
- **Matplotlib backend issues**: On headless systems, matplotlib may need a non-interactive backend (already configured in the code)

## Frontend Dependencies

### Prerequisites
- Node.js 18+ (for npm)
- npm (comes with Node.js)

### Installation Steps

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install frontend dependencies**:
   ```bash
   npm install
   ```

### Required Packages

The frontend requires the following packages (see `frontend/package.json`):

- **React**: ^18.2.0
- **TypeScript**: ^5.2.2
- **Vite**: ^5.0.8 (build tool)
- **Axios**: ^1.6.0 (HTTP client)
- **Plotly.js**: ^2.26.0 (for interactive plots)
- **react-plotly.js**: ^2.6.0 (React wrapper for Plotly)

### Development

Run the frontend dev server:
```bash
cd frontend
npm run dev
```

This will start the Vite dev server on `http://127.0.0.1:5173` with proxy to backend at `http://127.0.0.1:8000`.

### Building for Production

Build static assets:
```bash
cd frontend
npm run build
```

This creates the `frontend/dist` directory with production-ready static files.

