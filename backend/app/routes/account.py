from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.alpaca_client import AlpacaCredentialError, AlpacaGateway
from app.dependencies import get_alpaca_gateway

router = APIRouter(prefix="/api", tags=["account"])


@router.get("/account")
def get_account(gateway: AlpacaGateway = Depends(get_alpaca_gateway)) -> dict[str, Any]:
    return _guard(gateway.account)


@router.get("/clock")
def get_clock(gateway: AlpacaGateway = Depends(get_alpaca_gateway)) -> dict[str, Any]:
    return _guard(gateway.clock)


@router.get("/positions")
def get_positions(gateway: AlpacaGateway = Depends(get_alpaca_gateway)) -> list[dict[str, Any]]:
    return _guard(gateway.positions)


@router.get("/orders")
def get_orders(gateway: AlpacaGateway = Depends(get_alpaca_gateway)) -> list[dict[str, Any]]:
    return _guard(gateway.orders)


def _guard(fetch):
    try:
        return fetch()
    except AlpacaCredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Alpaca request failed: {exc}") from exc
