# wichteln

A modern Secret Santa experience built with FastAPI and a festive React frontend. Create groups with whimsical three-word identifiers, apply gifting constraints, and let participants reveal their match without spoilers.

## Features
- **Identifier-based groups**: Spin up an exchange with any PascalCase three-word identifier (e.g. `CozyPineMittens`) that participants can use later.
- **Constraint-aware matching**: Prevent specific pairings (partners, roommates, etc.) while still producing fair matches.
- **JSON-first backend**: A clean API under `/api` powers the React app and makes automation/simple integrations straightforward.
- **Static React spa**: Cute, minimal, Christmas themed UI built with Vite + React, ready for static hosting on Vercel, Netlify, or GitHub Pages.
- **Legacy admin screens**: The original server-rendered HTML flows remain optionally available for email-based exchanges.

## Backend Quick Start

```bash
# Install Python dependencies (requires Python 3.10+)
uv sync

# Run the FastAPI server
uv run uvicorn wichteln.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend exposes the JSON API on `http://localhost:8000/api` and, if a production build of the frontend is present (`frontend/dist`), also serves the SPA on `http://localhost:8000/`.

## Frontend (React) Quick Start

```bash
cd frontend
npm install
npm run dev
```

By default the dev server runs on <http://localhost:5173>. Set `VITE_API_BASE_URL=http://localhost:8000` when you need the frontend to talk to a remote backend.

To produce a static bundle (for Vercel/Netlify/GitHub Pages):

```bash
npm run build
```

The build output lives in `frontend/dist` and can be deployed directly.

## How It Works

1. **Create a group:** Pick a PascalCase identifier, paste your participant names, and optionally add forbidden giver → receiver pairs.
2. **Share the identifier:** Only the identifier is needed—no codes or emails required.
3. **Reveal assignments:** Participants enter the identifier and their own name to see who they are gifting.
4. **(Optional) Legacy flow:** Set `ENABLE_LEGACY_ROUTES=true` to re-enable the original HTML admin pages for email-based workflows at `/legacy`.

## API Overview

- `POST /api/groups`  
  Create a new exchange. Body:
  ```json
  {
    "identifier": "CozyPineMittens",
    "participants": [{ "name": "Jamie" }, { "name": "Alex" }],
    "illegalPairs": [{ "giver": "Jamie", "receiver": "Alex" }],
    "description": "Optional notes"
  }
  ```

- `POST /api/groups/{identifier}/reveal`  
  Reveal a participant’s assigned recipient. Body:
  ```json
  { "name": "Jamie" }
  ```

- `GET /api/health`  
  Simple readiness probe.

Error responses follow FastAPI’s usual `{"detail": "..."}` shape.

## Configuration

| Variable | Purpose |
| --- | --- |
| `FRONTEND_ORIGINS` | Comma-separated list of origins allowed by CORS. Defaults to `*` for easy local dev. |
| `ENABLE_LEGACY_ROUTES` | Set to `true` to expose the original HTML UI under `/legacy`. |
| `DATABASE_URL` | Optional SQLAlchemy connection string (defaults to SQLite `sqlite+aiosqlite:///./wichteln.db`). |
| `VITE_API_BASE_URL` | Frontend-only; set during build/runtime so the SPA knows where to send API requests. |

SMTP configuration (`SMTP_SERVER`, `SMTP_PORT`, `SENDER_EMAIL`, `SENDER_PASSWORD`) is still supported for the legacy email workflow.

## Deployment Notes

- **Backend**: Deploy like any FastAPI application (Dockerfile provided). The server automatically serves the built frontend from `frontend/dist` when those assets are present.
- **Frontend-only hosting**: Run `npm run build`, upload `frontend/dist` to a static host (Vercel, Netlify, etc.), and set `VITE_API_BASE_URL` to your backend URL.
- **Vercel**: Create a Vite project on Vercel pointing to `frontend`, set a build command of `npm run build`, and configure the `VITE_API_BASE_URL` environment variable.

## Development Tooling

- **Backend**: FastAPI, SQLAlchemy 2.x, SQLite (default)
- **Frontend**: Vite, React 18, React Router 6, TypeScript
- **Testing**: pytest / pytest-asyncio (backend)

Run backend tests with:

```bash
uv run pytest
```

## License

MIT
