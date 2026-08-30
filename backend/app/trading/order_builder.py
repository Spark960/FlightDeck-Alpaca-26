from __future__ import annotations

from typing import Any


def build_close_order_payload(position: dict[str, Any], client_order_id: str, qty: int | None = None) -> dict[str, Any]:
    symbol = position["symbol"]
    position_qty = abs(int(float(position.get("qty") or 1)))
    close_qty = qty or position_qty
    side = "sell" if float(position.get("qty") or 0) > 0 else "buy"
    limit_price = _position_midpoint(position)
    return {
        "client_order_id": client_order_id,
        "type": "limit",
        "time_in_force": "day",
        "symbol": symbol,
        "qty": close_qty,
        "side": side,
        "limit_price": limit_price,
        "position_intent": "sell_to_close" if side == "sell" else "buy_to_close",
    }


def _position_midpoint(position: dict[str, Any]) -> float:
    market_value = abs(float(position.get("market_value") or 0))
    qty = abs(float(position.get("qty") or 1))
    if market_value and qty:
        per_share = (market_value / qty) / 100
        return round(max(per_share, 0.01), 2)
    return 0.01


def build_order_payload(proposal: dict[str, Any], client_order_id: str, qty: int = 1) -> dict[str, Any]:
    legs = proposal.get("legs") or []
    if not legs:
        raise ValueError("Proposal has no option legs.")

    strategy_type = str(proposal.get("strategy_type") or "")
    if strategy_type in {"long_call", "long_put"}:
        return _build_single_leg_order(legs[0], client_order_id, qty)
    if len(legs) != 2:
        raise ValueError("Debit spread proposals must contain exactly two legs.")
    return _build_spread_order(legs, client_order_id, qty)


def _build_single_leg_order(leg: dict[str, Any], client_order_id: str, qty: int) -> dict[str, Any]:
    side = str(leg.get("side") or "buy").lower()
    return {
        "client_order_id": client_order_id,
        "type": "limit",
        "time_in_force": "day",
        "symbol": leg["symbol"],
        "qty": qty,
        "side": side,
        "limit_price": _midpoint(leg["bid"], leg["ask"]),
        "position_intent": "buy_to_open" if side == "buy" else "sell_to_open",
    }


def _build_spread_order(legs: list[dict[str, Any]], client_order_id: str, qty: int) -> dict[str, Any]:
    order_legs = []
    for leg in legs:
        side = str(leg.get("side") or "").lower()
        order_legs.append(
            {
                "symbol": leg["symbol"],
                "side": side,
                "ratio_qty": 1,
                "position_intent": "buy_to_open" if side == "buy" else "sell_to_open",
            }
        )

    return {
        "client_order_id": client_order_id,
        "type": "limit",
        "time_in_force": "day",
        "order_class": "mleg",
        "qty": qty,
        "limit_price": _net_debit_limit(legs),
        "legs": order_legs,
    }


def _net_debit_limit(legs: list[dict[str, Any]]) -> float:
    total = 0.0
    for leg in legs:
        midpoint = _midpoint(leg.get("bid"), leg.get("ask"))
        if str(leg.get("side")).lower() == "buy":
            total += midpoint
        else:
            total -= midpoint
    return round(max(total, 0.01), 2)


def _midpoint(bid: Any, ask: Any) -> float:
    bid_value = float(bid)
    ask_value = float(ask)
    return round((bid_value + ask_value) / 2, 2)
