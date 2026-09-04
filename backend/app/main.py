from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.config import get_settings
from app.db import init_db
from app.routes import account, audit, integrations, market, monitor, options, proposals, risk, scan, trades
from app.scheduler import on_shutdown, on_startup

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await on_startup()
    try:
        yield
    finally:
        await on_shutdown()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Autonomous paper-trading options agent with deterministic risk gates.",
    lifespan=lifespan,
)

# When the SPA is served from the same origin (production), CORS is a no-op
# because the browser sees same-origin requests. We still honour the
# ``CORS_ORIGINS`` list so local Vite dev (http://localhost:5173) keeps
# working, and so external judges can hit the API from a notebook if they
# prefer to use the JSON directly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(account.router)
app.include_router(audit.router)
app.include_router(market.router)
app.include_router(options.router)
app.include_router(proposals.router)
app.include_router(risk.router)
app.include_router(scan.router)
app.include_router(trades.router)
app.include_router(monitor.router)
app.include_router(integrations.router)


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "paper_mode": settings.alpaca_paper,
        "demo_mode": settings.demo_mode,
    }


@app.get("/api/settings")
def public_settings() -> dict[str, object]:
    return {
        "app": settings.app_name,
        "environment": settings.environment,
        "paper_mode": settings.alpaca_paper,
        "demo_mode": settings.demo_mode,
        "alpaca_credentials_configured": settings.has_alpaca_credentials,
        "alpaca_trading_base_url": settings.alpaca_trading_base_url,
        "alpaca_data_base_url": settings.alpaca_data_base_url,
        "agent_credentials_configured": settings.has_agent_credentials,
        "agent_base_url": settings.agent_base_url,
        "agent_model": settings.agent_model,
        "alpaca_cli_binary": settings.alpaca_cli_binary,
        "scheduler_enabled": settings.scheduler_enabled,
        "scheduler_interval_minutes": settings.scheduler_interval_minutes,
    }


# ---------------------------------------------------------------------------
# Static SPA mount
# ---------------------------------------------------------------------------
# The Vite build output (``frontend/dist``) is shipped inside the Docker
# image at ``STATIC_DIR`` (default ``backend/static``). When the directory is
# present we serve the bundle from the same origin so the cockpit and the API
# share one URL, and we fall back to ``index.html`` for client-side routes
# so the React Router URLs survive a hard refresh.
_STATIC_DIR = Path(settings.static_dir) if settings.static_dir else None
if _STATIC_DIR is not None and _STATIC_DIR.is_dir():
    _INDEX_HTML = _STATIC_DIR / "index.html"

    @app.get("/", include_in_schema=False)
    def root_index() -> FileResponse:
        return FileResponse(_INDEX_HTML)

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str) -> FileResponse:
        # Serve a real file if it exists (e.g. /assets/index-XXX.js,
        # /favicon.svg); otherwise return index.html so the React Router
        # can take over. We never return 404 for unknown routes because
        # the SPA legitimately owns those URLs.
        if full_path:
            candidate = (_STATIC_DIR / full_path).resolve()
            try:
                candidate.relative_to(_STATIC_DIR.resolve())
            except ValueError:
                # Path traversal attempt; just send index.html.
                return FileResponse(_INDEX_HTML)
            if candidate.is_file():
                return FileResponse(candidate)
        return FileResponse(_INDEX_HTML)
