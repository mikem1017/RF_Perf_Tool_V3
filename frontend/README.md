# RF Performance Tool - Frontend

React + TypeScript frontend for the RF Performance Tool.

## Setup

Install dependencies:
```bash
npm install
```

## Development

Start the development server:
```bash
npm run dev
```

The dev server runs on `http://127.0.0.1:5173` and proxies API requests to `http://127.0.0.1:8000`.

## Build

Build for production:
```bash
npm run build
```

Outputs to `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── services/    # API client service
│   ├── components/  # React components (to be implemented)
│   ├── App.tsx      # Main app component
│   └── main.tsx     # Entry point
├── package.json
├── vite.config.ts   # Vite configuration
└── tsconfig.json    # TypeScript configuration
```

## API Client

All API communication goes through `src/services/api.ts`. The API client:
- Uses axios for HTTP requests
- Handles errors consistently
- Proxies requests to backend in dev mode
- Provides typed endpoints for all backend routes

## Notes

- All business logic is in the backend
- Frontend only displays backend-computed results
- No business logic in frontend components
- Uses Plotly.js for interactive plots
- Backend-generated PNGs displayed directly


