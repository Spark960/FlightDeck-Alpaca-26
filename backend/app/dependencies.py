from functools import lru_cache

from app.alpaca_client import AlpacaGateway
from app.config import get_settings


@lru_cache
def get_alpaca_gateway() -> AlpacaGateway:
    return AlpacaGateway(get_settings())
