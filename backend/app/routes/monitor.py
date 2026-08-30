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
    get_proposal,
    has_recent_monitor_action,
    list_agent_events,
    list_orders,
    record_agent_event,
    record_order,
    record_position_snapshot,
)
from app.trading.monitor import run_monitor
from app.trading.order_builder import build_close_order_payload
from app.trading.order_sync import sync_open_orders, sync_order

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


class MonitorDecision(BaseModel):
    symbol: str
    action: str
    reason: str
    priority: int
    should_close: bool
    metrics: dict[str, Any]


class MonitorResponse(BaseModel):
    run_id: str
    timestamp: str
    account: dict[str, Any]
    position_count: int
    open_order_count: int
    decisions: list[MonitorDecision]
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, Any]
    synced_orders: list[dict[str, Any]] = Field(default_factory=list)
    executed_closes: list[dict[str, Any]] = Field(default_factory=list)


@router.post("/run", response_model=MonitorResponse)
def run_position_monitor(
    sync_orders: bool = Query(default=True),
    execute_closes: bool = Query(default=False),
    dry_run: bool = Query(default=True),
    gateway: AlpacaGateway = Depends(get_alpaca_gateway),
) -> MonitorResponse:
    settings = get_settings()
    run_id = create_run("position_monitor", {"sync_orders": sync_orders, "execute_closes": execute_closes})
    try:
        account = gateway.account()
        positions = gateway.positions()
        orders = gateway.orders()
        record_position_snapshot(run_id, {"positions": positions, "account": account})

        synced: list[dict[str, Any]] = []
        if sync_orders:
            synced = sync_open_orders(gateway)

        stored_orders = list_orders(limit=100)
        proposals_by_id = _load_proposals(stored_orders)
        recent_actions = _recent_monitor_actions(settings.monitor_action_cooldown_hours)

        result = run_monitor(
            account,
            positions,
            stored_orders,
            proposals_by_id,
            settings,
            recent_actions=recent_actions,
        )

        executed_closes: list[dict[str, Any]] = []
        for decision in result["decisions"]:
            record_agent_event(
                "monitor_decision",
                decision,
                run_id=run_id,
            )
            if not decision.get("should_close"):
                continue
            if execute_closes and not has_recent_monitor_action(
                decision["symbol"],
                decision["action"],
                settings.monitor_action_cooldown_hours,
            ):
                close_result = _execute_close(
                    gateway,
                    run_id,
                    decision,
                    positions,
                    dry_run=dry_run,
                )
                executed_closes.append(close_result)

        for alert in result["alerts"]:
            record_agent_event("monitor_alert", alert, run_id=run_id)

        complete_run(
            run_id,
            {
                "position_count": result["position_count"],
                "summary": result["summary"],
                "synced_order_count": len(synced),
                "executed_close_count": len(executed_closes),
            },
        )
        return MonitorResponse(
            run_id=run_id,
            synced_orders=synced,
            executed_closes=executed_closes,
            **result,
        )
    except AlpacaCredentialError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Monitor run failed: {exc}") from exc


@router.get("/latest")
def latest_monitor_events(limit: int = Query(default=20, ge=1, le=200)) -> dict[str, Any]:
    decisions = list_agent_events(event_type="monitor_decision", limit=limit)
    alerts = list_agent_events(event_type="monitor_alert", limit=limit)
    actions = list_agent_events(event_type="monitor_action", limit=limit)
    return {
        "decisions": decisions,
        "alerts": alerts,
        "actions": actions,
    }


def _load_proposals(stored_orders: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    proposals: dict[str, dict[str, Any]] = {}
    for order in stored_orders:
        proposal_id = order.get("proposal_id")
        if not proposal_id or proposal_id in proposals:
            continue
        proposal = get_proposal(proposal_id)
        if proposal is not None:
            proposals[proposal_id] = proposal
    return proposals


def _recent_monitor_actions(cooldown_hours: int) -> dict[str, set[str]]:
    recent: dict[str, set[str]] = {}
    for event in list_agent_events(event_type="monitor_action", limit=200):
        payload = event.get("payload") or {}
        symbol = payload.get("symbol")
        action = payload.get("action")
        if not symbol or not action:
            continue
        if has_recent_monitor_action(str(symbol), str(action), cooldown_hours):
            recent.setdefault(str(symbol), set()).add(str(action))
    return recent


def _execute_close(
    gateway: AlpacaGateway,
    run_id: str,
    decision: dict[str, Any],
    positions: list[dict[str, Any]],
    *,
    dry_run: bool,
) -> dict[str, Any]:
    symbol = decision["symbol"]
    position = next((item for item in positions if item.get("symbol") == symbol), None)
    if position is None:
        return {"symbol": symbol, "action": decision["action"], "error": "position_not_found"}

    close_client_id = client_order_id(run_id, f"CLOSE-{symbol}")
    payload = build_close_order_payload(position, close_client_id)

    if dry_run:
        record_agent_event(
            "monitor_action",
            {"symbol": symbol, "action": decision["action"], "dry_run": True, "order_payload": payload},
            run_id=run_id,
        )
        return {
            "symbol": symbol,
            "action": decision["action"],
            "dry_run": True,
            "order_payload": payload,
        }

    response = gateway.submit_order(payload)
    order_id = record_order(run_id, close_client_id, payload, response)
    record_agent_event(
        "monitor_action",
        {
            "symbol": symbol,
            "action": decision["action"],
            "dry_run": False,
            "order_id": order_id,
            "order_status": response.get("status"),
        },
        run_id=run_id,
    )
    return {
        "symbol": symbol,
        "action": decision["action"],
        "dry_run": False,
        "order_id": order_id,
        "alpaca_response": response,
    }
