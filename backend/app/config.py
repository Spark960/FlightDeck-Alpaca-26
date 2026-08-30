from functools import lru_cache
from pathlib import Path

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
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

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
