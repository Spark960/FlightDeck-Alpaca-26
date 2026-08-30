from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.alpaca_client import AlpacaCredentialError, AlpacaGateway
from app.dependencies import get_alpaca_gateway
from app.storage.audit import (
    complete_run,
    create_run,
    record_agent_event,
    record_market_snapshot,
)
from app.trading.signals import no_trade_candidate, rank_candidates
from app.trading.universe import LIQUID_UNIVERSE

router = APIRouter(prefix="/api", tags=["scan"])


class ScanRequest(BaseModel):
    symbols: list[str] | None = Field(default=None)
    limit: int = Field(default=5, ge=1, le=25)


@router.post("/scan")
def scan_market(
    request: ScanRequest | None = None,
    gateway: AlpacaGateway = Depends(get_alpaca_gateway),
) -> dict[str, Any]:
    scan_request = request or ScanRequest()
    symbols = [symbol.upper() for symbol in (scan_request.symbols or LIQUID_UNIVERSE)]
    run_id = create_run("market_scan", {"symbols": symbols})

    try:
        snapshots = gateway.stock_snapshots(symbols)
        historical_bars = gateway.stock_bars(symbols, days=30)
        candidates = rank_candidates(snapshots, historical_bars)
        selected = candidates[: scan_request.limit]
        if not selected or selected[0]["direction"] == "none":
            selected.append(no_trade_candidate("no_candidate_cleared_minimum_score"))

        payload = {
            "run_id": run_id,
            "universe": symbols,
            "candidates": selected,
            "candidate_count": len(selected),
        }
        record_market_snapshot(run_id, symbols, {"snapshots": snapshots, "historical_bars": historical_bars})
        record_agent_event("market_scan_ranked", payload, run_id=run_id)
        complete_run(run_id, {"candidate_count": len(selected), "top_symbol": selected[0]["symbol"]})
        return payload
    except AlpacaCredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market scan failed: {exc}") from exc
