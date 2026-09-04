from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv
from pydantic import Field
from pydantic.dataclasses import dataclass

ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ROOT_ENV)


@dataclass(frozen=True)
class Settings:
    app_name: str = Field(default="FlightDeck Alpha")
    environment: str = Field(default="development")
    demo_mode: bool = Field(default=True)
    alpaca_api_key: str | None = Field(default=None)
    alpaca_secret_key: str | None = Field(default=None)
    alpaca_paper: bool = Field(default=True)
    alpaca_trading_base_url: str = Field(default="https://paper-api.alpaca.markets/v2")
    alpaca_data_base_url: str = Field(default="https://data.alpaca.markets")
    database_url: str = Field(default="sqlite:///./flightdeck_alpha.db")
    agent_api_key: str | None = Field(default=None)
    agent_base_url: str = Field(default="https://generativelanguage.googleapis.com/v1beta/openai/")
    agent_model: str = Field(default="gemini-3.7-flash")
    max_risk_per_trade_pct: float = Field(default=1.5)
    max_daily_loss_pct: float = Field(default=3.0)
    max_drawdown_pct: float = Field(default=8.0)
    max_open_option_trades: int = Field(default=5)
    max_same_underlying_trades: int = Field(default=2)
    max_total_premium_pct: float = Field(default=20.0)
    take_profit_pct: float = Field(default=50.0)
    stop_loss_pct: float = Field(default=50.0)
    time_stop_days: int = Field(default=14)
    expiration_risk_days: int = Field(default=3)
    monitor_action_cooldown_hours: int = Field(default=24)
    alpaca_cli_binary: str = Field(default="alpaca")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    scheduler_enabled: bool = Field(default=False)
    scheduler_interval_minutes: int = Field(default=15, ge=1, le=240)
    scheduler_market_hours_only: bool = Field(default=True)
    static_dir: str | None = Field(default=None)

    @property
    def has_alpaca_credentials(self) -> bool:
        return bool(self.alpaca_api_key and self.alpaca_secret_key)

    @property
    def has_agent_credentials(self) -> bool:
        return bool(self.agent_api_key)


@lru_cache
def get_settings() -> Settings:
    import os

    return Settings(
        app_name=os.getenv("APP_NAME", "FlightDeck Alpha"),
        environment=os.getenv("ENVIRONMENT", "development"),
        demo_mode=_env_bool("DEMO_MODE", default=True),
        alpaca_api_key=_env_str("ALPACA_API_KEY"),
        alpaca_secret_key=_env_str("ALPACA_SECRET_KEY"),
        alpaca_paper=_env_bool("ALPACA_PAPER", default=True),
        alpaca_trading_base_url=_env_str(
            "ALPACA_TRADING_BASE_URL", "https://paper-api.alpaca.markets/v2"
        ),
        alpaca_data_base_url=_env_str(
            "ALPACA_DATA_BASE_URL", "https://data.alpaca.markets"
        ),
        database_url=_env_str("DATABASE_URL", "sqlite:///./flightdeck_alpha.db"),
        agent_api_key=_env_str("GEMINI_API_KEY") or _env_str("OPENAI_API_KEY"),
        agent_base_url=_env_str(
            "AGENT_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"
        ),
        agent_model=_env_str("AGENT_MODEL", "gemini-3.7-flash"),
        max_risk_per_trade_pct=_env_float("MAX_RISK_PER_TRADE_PCT", 1.5),
        max_daily_loss_pct=_env_float("MAX_DAILY_LOSS_PCT", 3.0),
        max_drawdown_pct=_env_float("MAX_DRAWDOWN_PCT", 8.0),
        max_open_option_trades=_env_int("MAX_OPEN_OPTION_TRADES", 5),
        max_same_underlying_trades=_env_int("MAX_SAME_UNDERLYING_TRADES", 2),
        max_total_premium_pct=_env_float("MAX_TOTAL_PREMIUM_PCT", 20.0),
        take_profit_pct=_env_float("TAKE_PROFIT_PCT", 50.0),
        stop_loss_pct=_env_float("STOP_LOSS_PCT", 50.0),
        time_stop_days=_env_int("TIME_STOP_DAYS", 14),
        expiration_risk_days=_env_int("EXPIRATION_RISK_DAYS", 3),
        monitor_action_cooldown_hours=_env_int("MONITOR_ACTION_COOLDOWN_HOURS", 24),
        alpaca_cli_binary=_env_str("ALPACA_CLI_BINARY", "alpaca") or "alpaca",
        scheduler_enabled=_env_bool("SCHEDULER_ENABLED", default=False),
        scheduler_interval_minutes=_env_int("SCHEDULER_INTERVAL_MINUTES", 15),
        static_dir=_env_str("STATIC_DIR")
        or (
            str(Path(__file__).resolve().parents[2] / "frontend" / "dist")
            if (Path(__file__).resolve().parents[2] / "frontend" / "dist").is_dir()
            else (
                str(Path(__file__).resolve().parents[1] / "static")
                if (Path(__file__).resolve().parents[1] / "static").is_dir()
                else None
            )
        ),
    )


def _env_bool(name: str, default: bool) -> bool:
    import os

    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_str(name: str, default: str | None = None) -> str | None:
    import os

    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip()
    return value or default


def _env_float(name: str, default: float) -> float:
    import os

    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    import os

    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default
