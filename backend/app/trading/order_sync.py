from __future__ import annotations

from typing import Any

from app.alpaca_client import AlpacaGateway
from app.storage.audit import (
    TERMINAL_ORDER_STATUSES,
    get_order,
    list_orders_needing_sync,
    record_agent_event,
    update_order_response,
)


def classify_order_status(response: dict[str, Any]) -> dict[str, Any]:
    status = str(response.get("status") or "unknown").lower()
    filled_qty = _qty(response.get("filled_qty"))
    order_qty = _qty(response.get("qty"))
    is_partial = status == "partially_filled" or (
        filled_qty is not None and order_qty is not None and 0 < filled_qty < order_qty
    )
    is_rejected = status in {"rejected", "expired", "canceled", "cancelled"}
    is_filled = status == "filled" or (
        filled_qty is not None and order_qty is not None and filled_qty >= order_qty > 0
    )
    is_terminal = status in TERMINAL_ORDER_STATUSES or is_filled or is_rejected

    return {
        "status": status,
        "filled_qty": filled_qty,
        "order_qty": order_qty,
        "is_partial": is_partial,
        "is_rejected": is_rejected,
        "is_filled": is_filled,
        "is_terminal": is_terminal,
    }


def sync_order(gateway: AlpacaGateway, order_id: str) -> dict[str, Any]:
    stored = get_order(order_id)
    if stored is None:
        raise ValueError(f"Order {order_id} was not found in the audit log.")

    previous = stored.get("response") or {}
    latest = gateway.get_order(order_id)
    merged = {**previous, **latest}
    update_order_response(order_id, merged)
    summary = classify_order_status(merged)

    record_agent_event(
        "order_status_sync",
        {
            "order_id": order_id,
            "proposal_id": stored.get("proposal_id"),
            "previous_status": previous.get("status"),
            "current_status": summary["status"],
            **summary,
        },
        run_id=stored.get("run_id"),
    )
    return {
        "order_id": order_id,
        "proposal_id": stored.get("proposal_id"),
        "previous_status": previous.get("status"),
        "response": merged,
        **summary,
    }


def sync_open_orders(gateway: AlpacaGateway, limit: int = 50) -> list[dict[str, Any]]:
    pending = list_orders_needing_sync(limit=limit)
    return [sync_order(gateway, order["order_id"]) for order in pending]


def _qty(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
