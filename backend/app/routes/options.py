from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.alpaca_client import AlpacaCredentialError, AlpacaGateway
from app.dependencies import get_alpaca_gateway

router = APIRouter(prefix="/api/options", tags=["options"])


@router.get("/contracts/{symbol}")
def get_option_contracts(
    symbol: str,
    gateway: AlpacaGateway = Depends(get_alpaca_gateway),
) -> dict[str, Any]:
    try:
        return gateway.option_contracts(symbol.upper())
    except AlpacaCredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Alpaca options contract request failed: {exc}") from exc


@router.get("/chain/{symbol}")
def get_option_chain(
    symbol: str,
    gateway: AlpacaGateway = Depends(get_alpaca_gateway),
) -> dict[str, Any]:
    try:
        return gateway.option_chain(symbol.upper())
    except AlpacaCredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Alpaca options chain request failed: {exc}") from exc
