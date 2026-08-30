from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.alpaca_client import AlpacaCredentialError, AlpacaGateway
from app.dependencies import get_alpaca_gateway
from app.storage.audit import (
    complete_run,
    create_run,
    record_agent_event,
    record_option_chain,
    record_trade_proposal,
)
from app.trading.option_selector import select_debit_spread

router = APIRouter(prefix="/api/proposals", tags=["proposals"])


class ProposalRequest(BaseModel):
    symbol: str = Field(default="SPY")
    direction: str = Field(default="bullish", pattern="^(bullish|bearish)$")
    max_debit: float = Field(default=1500.0, gt=0)


@router.post("")
def create_proposal(
    request: ProposalRequest,
    gateway: AlpacaGateway = Depends(get_alpaca_gateway),
) -> dict[str, Any]:
    symbol = request.symbol.upper()
    run_id = create_run("trade_proposal", {"symbol": symbol, "direction": request.direction})

    try:
        contracts = gateway.option_contracts(symbol)
        chain = gateway.option_chain(symbol)
        proposal = select_debit_spread(
            symbol=symbol,
            direction=request.direction,
            contracts_payload=contracts,
            chain_payload=chain,
            max_debit=request.max_debit,
        )

        record_option_chain(run_id, symbol, {"contracts": contracts, "chain": chain})
        if proposal["accepted"]:
            proposal_id = record_trade_proposal(run_id, proposal)
            proposal["proposal_id"] = proposal_id
        else:
            record_agent_event("trade_proposal_rejected", proposal, run_id=run_id)

        complete_run(
            run_id,
            {
                "symbol": symbol,
                "direction": request.direction,
                "accepted": proposal["accepted"],
            },
        )
        return {"run_id": run_id, **proposal}
    except AlpacaCredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Proposal generation failed: {exc}") from exc
