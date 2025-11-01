import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from wichteln.api_routes import api_router
from wichteln.database import init_db

app = FastAPI(title="Wichteln - Secret Santa Exchange")

frontend_origins = os.getenv("FRONTEND_ORIGINS", "")
allowed_origins = [origin.strip() for origin in frontend_origins.split(",") if origin.strip()]
if not allowed_origins:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_db()

app.include_router(api_router)

if os.getenv("ENABLE_LEGACY_ROUTES", "").lower() in {"1", "true", "yes"}:
    from wichteln.routes import router as legacy_router  # noqa: WPS433 (import within block)

    app.include_router(legacy_router, prefix="/legacy", tags=["legacy"])

DIST_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if DIST_DIR.exists():
    assets_dir = DIST_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    async def serve_frontend_root() -> FileResponse:
        return FileResponse(DIST_DIR / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        blocked_prefixes = ("api", "assets", "docs", "openapi.json", "redoc")
        if full_path.startswith(blocked_prefixes):
            raise HTTPException(status_code=404)
        index_path = DIST_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        raise HTTPException(status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("wichteln.main:app", host="0.0.0.0", port=8000, reload=True)
