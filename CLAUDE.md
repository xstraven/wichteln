# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Wichteln** is a Secret Santa gift exchange web app with:
- **Backend**: FastAPI with async PostgreSQL (Neon) and JSONB storage
- **Frontend**: React 18 + TypeScript with Vite, deployed as a static SPA
- **Database**: Single-table schema (`secret_santa`) storing exchanges as JSON blobs
- **API**: Stateless REST endpoints under `/api` for creating exchanges and revealing matches

## Architecture & Data Flow

### Core Concepts

1. **Identifier-based groups**: Users create exchanges with PascalCase three-word identifiers (e.g., `CozyPineMittens`), generated from a hardcoded word bank of 50 words per category (125,000 combinations).
2. **Participants as flat list**: Each exchange stores participants as a simple array of strings `["Alice", "Bob"]` in the JSONB `santa` field.
3. **Constraint-aware matching**: The matching algorithm respects illegal giver→receiver pairs while ensuring no one draws themselves.
4. **Stateless reveals**: Participants enter their group identifier and name to look up their assigned recipient (no login required).

### Database Schema

Single table `secret_santa`:
```python
uuid: UUID (primary key, internal only)
human_id: String (unique, indexed; the user-facing identifier like "CozyPineMittens")
santa: JSON {
  "participants": ["Alice", "Bob", ...],
  "constraints": [{"giver": "Alice", "receiver": "Bob"}, ...],
  "matches": [{"giver": "Alice", "receiver": "Bob"}, ...],
  "description": "Optional notes"
}
created_at: DateTime
looked_at: DateTime (nullable; timestamp of last reveal)
```

### API Endpoints

- `POST /api/groups` – Create a new exchange
- `POST /api/groups/{identifier}/reveal` – Reveal a participant's assigned recipient
- `GET /api/health` – Readiness probe

See `README.md` for payload details.

## Development Commands

| Task | Command |
|------|---------|
| **Backend setup** | `uv sync` (install dependencies) |
| **Run backend (dev)** | `uv run uvicorn wichteln.main:app --reload` (port 8000) |
| **Run single test** | `uv run pytest tests/test_api.py::test_create_group_basic -v` |
| **Run all tests** | `uv run pytest` |
| **Frontend dev** | `cd frontend && npm install && npm run dev` (port 5173, proxies to backend at :8000) |
| **Frontend build** | `cd frontend && npm run build` (outputs to `frontend/dist`) |
| **Frontend preview** | `cd frontend && npm run preview` |

**Note**: Tests use async mode (`pytest-asyncio`); the backend creates a test database on each run via `tests/test_api.py:unique_identifier()`.

## Code Organization

### Backend (`wichteln/`)

- `main.py` – FastAPI app bootstrap, CORS, static file serving, lifespan events
- `api_routes.py` – Core REST endpoints (`POST /api/groups`, `POST /api/groups/{id}/reveal`)
- `routes.py` – **Legacy** HTML-based admin flows (conditional on `ENABLE_LEGACY_ROUTES=true`)
- `models.py` – SQLAlchemy model (`SecretSanta`)
- `schemas.py` – Pydantic request/response models and validators
- `database.py` – Async engine, session factory, database initialization
- `utils.py` – Helper functions:
  - `generate_secret_santa_matches()` – Random permutation-based matching with constraint support
  - `generate_unique_code()` – 5-letter uppercase code generator (used by legacy routes)
  - `validate_email()` – Basic email validator (legacy)

### Frontend (`frontend/src/`)

- `pages/CreateGroup.tsx` – Main form for setting up exchanges; includes word bank (50 words × 3 categories)
- `pages/Reveal.tsx` – Participant lookup form to reveal assigned recipient
- `pages/Result.tsx` – Display matched recipient
- `api/client.ts` – Fetch wrapper with types for `CreateGroupPayload`, `GroupCreateResponse`, `RevealResponse`
- `styles/` – Global CSS (scoped context-based naming)
- `App.tsx` – Router setup (React Router 6)

## Important Implementation Notes

### Participants Storage

After simplification, participants are stored as **flat strings** in the JSONB array:
```json
"participants": ["Alice", "Bob", "Charlie"]
```

**Not** as objects:
```json
"participants": [{"code": "UDCJY", "name": "Jamie"}]
```

This change:
- Simplifies schema and reduces storage overhead
- Eliminated the unused `code` field that was generated but never exposed via API
- The `uuid` field is generated but not exposed to clients; consider removing if not needed for internal operations

### Word Bank Expansion

The frontend word bank in `CreateGroup.tsx` (lines 10–32) has been expanded to **50 words per category**:
- **First category** (characters/attributes): Santa, Elf, Reindeer, etc.
- **Second category** (scents/flavors): Cinnamon, Nutmeg, Clementine, etc.
- **Third category** (decorations/traditions): Ornament, Tinsel, Garland, etc.

This yields **125,000 combinations** (50³), significantly reducing collision risk for identifiers.

### Matching Algorithm

The `generate_secret_santa_matches()` function uses a **random permutation approach**:
1. Shuffle participants randomly up to 1,000 attempts
2. Check each giver–receiver pair for conflicts:
   - Giver cannot equal receiver (no self-matches)
   - Giver→receiver must not violate illegal pair constraints
3. On success, return the matches dict
4. On failure after 1,000 attempts, fall back to simple rotation (may violate some constraints)

This is simple but adequate for small groups; for large groups with many constraints, a more sophisticated algorithm may be needed.

## Testing

Tests live in `tests/test_api.py` and cover:
- Happy paths (create group, reveal match)
- Validation (invalid identifiers, duplicates, insufficient participants)
- Case-insensitive lookups
- Constraint handling

**Key test helpers**:
- `unique_identifier()` – Generates a unique PascalCase identifier using UUID-seeded word selection
- `AsyncClient` from `httpx` – Test HTTP client for FastAPI

Run a single test:
```bash
uv run pytest tests/test_api.py::test_create_group_and_reveal -v
```

## Deployment

The app supports two deployment patterns:

### Single-Domain Deployment (Recommended)

The FastAPI backend automatically serves the built frontend from `frontend/dist`:
1. Build the frontend: `cd frontend && npm run build`
2. Deploy the backend normally (the app will serve static files from `frontend/dist`)
3. SPA routing is handled by `main.py:47-59` – all non-API routes serve `index.html`
4. Set `VITE_API_BASE_URL=/api` during build (or leave unset for relative URLs)

The backend blocks requests to `/api`, `/assets`, `/docs`, `/openapi.json`, and `/redoc` from being served as SPA routes.

### Separate Deployment

Deploy frontend and backend separately:
1. **Frontend**: Upload `frontend/dist` to a static host (e.g., Vercel)
   - The included `frontend/vercel.json` configures SPA routing for Vercel
   - Set `VITE_API_BASE_URL` to your backend URL at build time
2. **Backend**: Deploy FastAPI app to any host
   - Configure `FRONTEND_ORIGINS` to allow CORS from your frontend domain

## Configuration

Required environment variables:
- `POSTGRES_CONNECT_STRING` or `DATABASE_URL` – Neon PostgreSQL connection string

Optional:
- `FRONTEND_ORIGINS` – CORS allowed origins (default: `*`); comma-separated list
- `ENABLE_LEGACY_ROUTES` – Set to `true` to enable legacy HTML admin UI at `/legacy`
- `VITE_API_BASE_URL` – Frontend: API base URL (default: relative `/api` path for same-domain deploys)

## Key Files to Know

| File | Purpose |
|------|---------|
| `wichteln/api_routes.py` | Core API logic; start here for endpoint changes |
| `wichteln/schemas.py` | Validation rules (PascalCase regex, min/max lengths) |
| `frontend/src/pages/CreateGroup.tsx` | Word bank and identifier generation |
| `tests/test_api.py` | Integration tests; run these before commits |
| `pyproject.toml` | Dependencies and development tools |

## Recent Refactoring & Cleanup

1. **Dead code removal**:
   - Removed unused `slugify()` function from `utils.py`
   - Removed unused import of `slugify` from `api_routes.py`

2. **Participants simplification**:
   - Changed from objects `{"code": "...", "name": "..."}` to flat strings `"Alice"`
   - Reduced JSONB storage overhead
   - The UUID primary key is generated but not exposed; consider if it should be retained

3. **Word bank expansion**:
   - Extended from 7 words per category (343 combinations) to 50 per category (125,000 combinations)

## Debugging Tips

- **Database connection issues**: Check `POSTGRES_CONNECT_STRING` is set and Neon is accessible
- **Test failures**: Ensure you have run `uv sync` and that PostgreSQL is configured for async
- **Frontend API errors**: Check `VITE_API_BASE_URL` environment variable if backend is on a different host
- **CORS issues**: Adjust `FRONTEND_ORIGINS` in environment; default is `*`
- **Legacy routes not showing**: Set `ENABLE_LEGACY_ROUTES=true` in `.env`

## Before Committing

1. Run tests: `uv run pytest`
2. Check for unused imports or dead code
3. Verify identifier validation logic (both frontend regex and backend Pydantic validator)
4. Test the match reveal flow with constraints
5. Ensure no secrets are committed (check `.env` is in `.gitignore`)
