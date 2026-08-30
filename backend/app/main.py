from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import init_db
from app.routes import account, audit, market, monitor, options, proposals, risk, scan, trades

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Autonomous paper-trading options agent with deterministic risk gates.",
)

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


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "paper_mode": settings.alpaca_paper,
        "demo_mode": settings.demo_mode,
    }


@app.get("/api/settings")
def public_settings() -> dict[str, str | bool]:
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
    }
