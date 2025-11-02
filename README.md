# wichteln

A Secret Santa gift exchange web app. Create groups with PascalCase three-word identifiers, add gifting constraints, and reveal matches—no registration needed.

## Quick Start

### Backend
```bash
uv sync
uv run uvicorn wichteln.main:app --reload
# API: http://localhost:8000/api
```

### Frontend
```bash
cd frontend && npm install && npm run dev
# Dev server: http://localhost:5173
# Talks to backend at http://localhost:8000
```

Override the backend URL with `VITE_API_BASE_URL`:
```bash
VITE_API_BASE_URL=http://your-api-host npm run dev
```

Production build:
```bash
npm run build  # Output: frontend/dist
```

## How It Works

1. **Create**: Pick a 3-word PascalCase identifier (e.g. `CozyPineMittens`), add participants and optional constraints.
2. **Share**: Only the identifier is needed.
3. **Reveal**: Participants enter the identifier and their name to see who they're gifting.

## API

- `POST /api/groups` – Create exchange
- `POST /api/groups/{identifier}/reveal` – Reveal recipient
- `GET /api/health` – Health check

See `CLAUDE.md` for full payload examples.

## Configuration

| Variable | Purpose |
|----------|---------|
| `POSTGRES_CONNECT_STRING` | **Required**: Neon PostgreSQL connection string |
| `VITE_API_BASE_URL` | Frontend: set to your backend URL (defaults to relative `/api` for same-domain deployments) |
| `FRONTEND_ORIGINS` | CORS origins (defaults to `*`) |
| `ENABLE_LEGACY_ROUTES` | Set `true` to enable legacy HTML UI at `/legacy` |

## Deployment

- **Single domain**: Backend serves both API and built frontend
  - Build frontend: `npm run build`
  - Deploy FastAPI app normally; it serves `frontend/dist` automatically
  - Set `VITE_API_BASE_URL=/api` at build time (or leave unset for relative URLs)

- **Separate backends**: Upload `frontend/dist` to static host, set `VITE_API_BASE_URL` to your API URL

## Tech Stack

- Backend: FastAPI, SQLAlchemy 2.x, Neon PostgreSQL
- Frontend: React 18, TypeScript, Vite
- Testing: pytest + pytest-asyncio

## License

MIT
