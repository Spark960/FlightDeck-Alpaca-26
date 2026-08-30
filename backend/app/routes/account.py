from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.alpaca_client import AlpacaCredentialError, AlpacaGateway
from app.dependencies import get_alpaca_gateway
from app.storage.audit import complete_run, create_run, record_position_snapshot

router = APIRouter(prefix="/api", tags=["account"])


@router.get("/account")
def get_account(gateway: AlpacaGateway = Depends(get_alpaca_gateway)) -> dict[str, Any]:
    return _guard(gateway.account)


@router.get("/clock")
def get_clock(gateway: AlpacaGateway = Depends(get_alpaca_gateway)) -> dict[str, Any]:
    return _guard(gateway.clock)


@router.get("/positions")
def get_positions(gateway: AlpacaGateway = Depends(get_alpaca_gateway)) -> list[dict[str, Any]]:
    return _guard_with_position_audit(gateway.positions)


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


def _guard_with_position_audit(fetch):
    try:
        run_id = create_run("position_snapshot")
        payload = fetch()
        record_position_snapshot(run_id, payload)
        complete_run(run_id, {"position_count": len(payload)})
        return payload
    except AlpacaCredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Alpaca request failed: {exc}") from exc
