from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.alpaca_client import AlpacaCredentialError, AlpacaGateway
from app.agents.analyst import analyze_and_critique
from app.config import get_settings
from app.dependencies import get_alpaca_gateway
from app.storage.audit import (
    complete_run,
    create_run,
    get_proposal,
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


class ProposalReviewRequest(BaseModel):
    proposal: dict[str, Any] | None = Field(default=None)
    proposal_id: str | None = Field(default=None)
    market_candidate: dict[str, Any] | None = Field(default=None)


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


@router.get("/{proposal_id}")
def get_trade_proposal(proposal_id: str) -> dict[str, Any]:
    proposal = get_proposal(proposal_id)
    if proposal is None:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} was not found.")
    return proposal


@router.post("/review")
def review_proposal(request: ProposalReviewRequest) -> dict[str, Any]:
    proposal = request.proposal
    source_proposal_id = request.proposal_id
    if source_proposal_id:
        stored = get_proposal(source_proposal_id)
        if stored is None:
            raise HTTPException(status_code=404, detail=f"Proposal {source_proposal_id} was not found.")
        proposal = stored["payload"]

    if proposal is None:
        raise HTTPException(status_code=400, detail="Provide proposal or proposal_id.")

    run_id = create_run("agent_review", {"proposal_id": source_proposal_id})
    review = analyze_and_critique(proposal, request.market_candidate, get_settings())
    payload = review.model_dump()
    record_agent_event("analyst_proposal", payload["analyst"], run_id=run_id)
    record_agent_event("critic_result", payload["critic"], run_id=run_id)
    complete_run(run_id, {"critic_passed": payload["critic"]["passed"], "source": payload["source"]})
    return {"run_id": run_id, "proposal_id": source_proposal_id, **payload}
