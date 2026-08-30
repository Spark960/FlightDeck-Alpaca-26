from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.alpaca_client import AlpacaCredentialError, AlpacaGateway
from app.config import get_settings
from app.dependencies import get_alpaca_gateway
from app.storage.audit import (
    client_order_id,
    complete_run,
    create_run,
    get_order,
    get_proposal,
    record_order,
    record_risk_check,
)
from app.trading.order_builder import build_order_payload
from app.trading.order_sync import sync_open_orders, sync_order
from app.trading.risk import evaluate_risk

router = APIRouter(prefix="/api/trades", tags=["trades"])


class ExecuteResponse(BaseModel):
    run_id: str
    proposal_id: str
    dry_run: bool
    risk_approved: bool
    order_payload: dict[str, Any] | None = None
    order_id: str | None = None
    alpaca_response: dict[str, Any] | None = None
    blocking_reasons: list[str] = Field(default_factory=list)


class OrderSyncResponse(BaseModel):
    run_id: str
    synced: list[dict[str, Any]]


class OrderStatusResponse(BaseModel):
    order_id: str
    stored: dict[str, Any] | None = None
    sync_result: dict[str, Any] | None = None


@router.post("/execute/{proposal_id}", response_model=ExecuteResponse)
def execute_trade(
    proposal_id: str,
    dry_run: bool = Query(default=True),
    gateway: AlpacaGateway = Depends(get_alpaca_gateway),
) -> ExecuteResponse:
    stored = get_proposal(proposal_id)
    if stored is None:
        raise HTTPException(status_code=404, detail=f"Proposal {proposal_id} was not found.")

    proposal = stored["payload"]
    if not proposal.get("accepted"):
        raise HTTPException(status_code=400, detail="Proposal was rejected and cannot be executed.")

    run_id = create_run("trade_execution", {"proposal_id": proposal_id, "dry_run": dry_run})
    try:
        account = gateway.account()
        clock = gateway.clock()
        positions = gateway.positions()
        risk_result = evaluate_risk(proposal, account, clock, positions, get_settings())
        record_risk_check(run_id, risk_result["approved"], risk_result, proposal_id=proposal_id)

        if not risk_result["approved"]:
            complete_run(
                run_id,
                {"proposal_id": proposal_id, "dry_run": dry_run, "approved": False},
            )
            return ExecuteResponse(
                run_id=run_id,
                proposal_id=proposal_id,
                dry_run=dry_run,
                risk_approved=False,
                blocking_reasons=risk_result["blocking_reasons"],
            )

        order_client_id = client_order_id(run_id, proposal.get("underlying_symbol", "OPT"))
        order_payload = build_order_payload(proposal, order_client_id)

        if dry_run:
            complete_run(
                run_id,
                {"proposal_id": proposal_id, "dry_run": True, "approved": True},
            )
            return ExecuteResponse(
                run_id=run_id,
                proposal_id=proposal_id,
                dry_run=True,
                risk_approved=True,
                order_payload=order_payload,
            )

        response = gateway.submit_order(order_payload)
        order_id = record_order(
            run_id,
            order_client_id,
            order_payload,
            response,
            proposal_id=proposal_id,
        )
        complete_run(
            run_id,
            {
                "proposal_id": proposal_id,
                "dry_run": False,
                "approved": True,
                "order_id": order_id,
                "order_status": response.get("status"),
            },
        )
        return ExecuteResponse(
            run_id=run_id,
            proposal_id=proposal_id,
            dry_run=False,
            risk_approved=True,
            order_payload=order_payload,
            order_id=order_id,
            alpaca_response=response,
        )
    except AlpacaCredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Trade execution failed: {exc}") from exc


@router.post("/sync", response_model=OrderSyncResponse)
def sync_orders(
    gateway: AlpacaGateway = Depends(get_alpaca_gateway),
) -> OrderSyncResponse:
    run_id = create_run("order_sync")
    try:
        synced = sync_open_orders(gateway)
        complete_run(run_id, {"synced_count": len(synced)})
        return OrderSyncResponse(run_id=run_id, synced=synced)
    except AlpacaCredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Order sync failed: {exc}") from exc


@router.get("/orders/{order_id}/status", response_model=OrderStatusResponse)
def get_order_status(
    order_id: str,
    refresh: bool = Query(default=False),
    gateway: AlpacaGateway = Depends(get_alpaca_gateway),
) -> OrderStatusResponse:
    stored = get_order(order_id)
    if stored is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} was not found.")

    sync_result = None
    if refresh:
        try:
            sync_result = sync_order(gateway, order_id)
            stored = get_order(order_id)
        except AlpacaCredentialError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Order refresh failed: {exc}") from exc

    return OrderStatusResponse(order_id=order_id, stored=stored, sync_result=sync_result)
