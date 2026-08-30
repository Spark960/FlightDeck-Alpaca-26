from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.alpaca_client import AlpacaCredentialError, AlpacaGateway
from app.config import get_settings
from app.dependencies import get_alpaca_gateway
from app.storage.audit import complete_run, create_run, get_proposal, record_risk_check
from app.trading.risk import evaluate_risk

router = APIRouter(prefix="/api/risk", tags=["risk"])


class RiskCheckRequest(BaseModel):
    proposal: dict[str, Any] | None = Field(default=None)
    proposal_id: str | None = Field(default=None)


@router.post("/check")
def check_risk(
    request: RiskCheckRequest,
    gateway: AlpacaGateway = Depends(get_alpaca_gateway),
) -> dict[str, Any]:
    proposal = request.proposal
    proposal_id = request.proposal_id
    if proposal_id:
        stored = get_proposal(proposal_id)
        if stored is None:
            raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} was not found.")
        proposal = stored["payload"]

    if proposal is None:
        raise HTTPException(status_code=400, detail="Provide proposal or proposal_id.")

    run_id = create_run("risk_check", {"proposal_id": proposal_id})
    try:
        account = gateway.account()
        clock = gateway.clock()
        positions = gateway.positions()
        result = evaluate_risk(proposal, account, clock, positions, get_settings())
        record_risk_check(run_id, result["approved"], result, proposal_id=proposal_id)
        complete_run(run_id, {"approved": result["approved"], "proposal_id": proposal_id})
        return {"run_id": run_id, "proposal_id": proposal_id, **result}
    except AlpacaCredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Risk check failed: {exc}") from exc
