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
    alpaca_trading_base_url: str = Field(default="https://paper-api.alpaca.markets")
    alpaca_data_base_url: str = Field(default="https://data.alpaca.markets")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    @property
    def has_alpaca_credentials(self) -> bool:
        return bool(self.alpaca_api_key and self.alpaca_secret_key)


@lru_cache
def get_settings() -> Settings:
    import os

    return Settings(
        app_name=os.getenv("APP_NAME", "FlightDeck Alpha"),
        environment=os.getenv("ENVIRONMENT", "development"),
        demo_mode=_env_bool("DEMO_MODE", default=True),
        alpaca_api_key=os.getenv("ALPACA_API_KEY") or None,
        alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY") or None,
        alpaca_paper=_env_bool("ALPACA_PAPER", default=True),
        alpaca_trading_base_url=os.getenv(
            "ALPACA_TRADING_BASE_URL", "https://paper-api.alpaca.markets"
        ),
        alpaca_data_base_url=os.getenv(
            "ALPACA_DATA_BASE_URL", "https://data.alpaca.markets"
        ),
    )


def _env_bool(name: str, default: bool) -> bool:
    import os

    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
