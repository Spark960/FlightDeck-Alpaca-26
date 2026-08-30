from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.alpaca_client import AlpacaCredentialError, AlpacaGateway
from app.dependencies import get_alpaca_gateway
from app.storage.audit import complete_run, create_run, record_option_chain

router = APIRouter(prefix="/api/options", tags=["options"])


@router.get("/contracts/{symbol}")
def get_option_contracts(
    symbol: str,
    gateway: AlpacaGateway = Depends(get_alpaca_gateway),
) -> dict[str, Any]:
    try:
        normalized_symbol = symbol.upper()
        run_id = create_run("option_contracts", {"symbol": normalized_symbol})
        payload = gateway.option_contracts(normalized_symbol)
        record_option_chain(run_id, normalized_symbol, payload)
        complete_run(run_id, {"symbol": normalized_symbol, "kind": "contracts"})
        return payload
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
        normalized_symbol = symbol.upper()
        run_id = create_run("option_chain", {"symbol": normalized_symbol})
        payload = gateway.option_chain(normalized_symbol)
        record_option_chain(run_id, normalized_symbol, payload)
        complete_run(run_id, {"symbol": normalized_symbol, "kind": "chain"})
        return payload
    except AlpacaCredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Alpaca options chain request failed: {exc}") from exc
