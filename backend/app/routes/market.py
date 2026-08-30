from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.alpaca_client import AlpacaCredentialError, AlpacaGateway
from app.dependencies import get_alpaca_gateway

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/snapshot")
def get_snapshots(
    symbols: str = Query(default="SPY,QQQ,AAPL"),
    gateway: AlpacaGateway = Depends(get_alpaca_gateway),
) -> dict[str, Any]:
    parsed_symbols = [symbol.strip().upper() for symbol in symbols.split(",") if symbol.strip()]
    if not parsed_symbols:
        raise HTTPException(status_code=400, detail="Provide at least one symbol.")

    try:
        return gateway.stock_snapshots(parsed_symbols)
    except AlpacaCredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Alpaca market data request failed: {exc}") from exc
