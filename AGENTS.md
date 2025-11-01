# Repository Guidelines

## Project Structure & Module Organization
- `wichteln/` hosts the FastAPI backend: `main.py` bootstraps the app, `api_routes.py` exposes JSON endpoints, `routes.py` keeps the legacy HTML flows, and `schemas.py` defines request/response models.
- `frontend/` contains the Vite + React SPA (`src/` for components, `src/pages/` for views, `src/api/` for API helpers, and `src/styles/` for global CSS). Build artefacts land in `frontend/dist/`.
- `static/` serves legacy assets, while `README.md` and `Dockerfile` document deployment options. SQLite state defaults to `wichteln.db` in the repo root.

## Build, Test, and Development Commands
- Backend setup: `uv sync` installs Python dependencies; `uv run uvicorn wichteln.main:app --reload` starts the API with hot reload.
- Backend tests: `uv run pytest` runs the current pytest suite (strict asyncio mode).
- Frontend dev server: `cd frontend && npm install && npm run dev` launches Vite on port 5173.
- Frontend production build: `npm run build` emits static assets to `frontend/dist`; serve locally with `npm run preview`.

## Coding Style & Naming Conventions
- Python code follows PEP 8 with 4-space indentation, type hints where practical, and FastAPI dependency-injection patterns.
- React/TypeScript uses 2-space indentation, functional components, and PascalCase filenames for components/pages (`CreateGroup.tsx`). CSS uses kebab-case class names scoped by context.
- Prefer descriptive identifiers (e.g., `illegalPairs`) and camelCase for JSON fields to mirror frontend expectations.

## Testing Guidelines
- Tests live under `tests/` (create the directory if expanding coverage). Use `pytest` + `pytest-asyncio` for async endpoints.
- Name new test modules `test_<feature>.py` and mark async tests with `@pytest.mark.asyncio`.
- When adding API routes, exercise both happy paths and validation failures using HTTPX test clients.

## Commit & Pull Request Guidelines
- Follow the existing concise, imperative style (`add frontend`, `simplify structure`). Capitalisation is optional but keep messages under ~60 characters.
- Reference relevant issues in the body when applicable and summarise behavioural changes plus verification steps.
- PRs should include: purpose summary, screenshots or curl/Vite output for UI/API changes, and explicit notes about required environment variables.

## Security & Configuration Tips
- Never commit secrets; rely on `.env` or deployment-specific config. `FRONTEND_ORIGINS` and `ENABLE_LEGACY_ROUTES` gate CORS and legacy views.
- Use non-production SMTP credentials when testing email workflows, and reset the bundled `wichteln.db` before sharing logs or samples.
