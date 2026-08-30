from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.config import Settings


def run_monitor(
    account: dict[str, Any],
    positions: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    proposals_by_id: dict[str, dict[str, Any]],
    settings: Settings,
    recent_actions: dict[str, set[str]] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    current_time = now or datetime.now(tz=UTC)
    recent = recent_actions or {}
    position_symbols = {str(position.get("symbol") or "") for position in positions}

    decisions: list[dict[str, Any]] = []
    alerts: list[dict[str, Any]] = []

    drawdown_alert = _drawdown_alert(account, settings)
    if drawdown_alert:
        alerts.append(drawdown_alert)

    for position in positions:
        decision = evaluate_position(
            position,
            orders=orders,
            proposals_by_id=proposals_by_id,
            position_symbols=position_symbols,
            settings=settings,
            recent_actions=recent,
            now=current_time,
        )
        decisions.append(decision)

    return {
        "timestamp": current_time.isoformat(),
        "account": {
            "equity": _money(account.get("equity") or account.get("portfolio_value")),
            "buying_power": _money(account.get("buying_power")),
            "portfolio_value": _money(account.get("portfolio_value")),
        },
        "position_count": len(positions),
        "open_order_count": len([order for order in orders if not _order_is_terminal(order)]),
        "decisions": decisions,
        "alerts": alerts,
        "summary": _summarize(decisions, alerts),
    }


def evaluate_position(
    position: dict[str, Any],
    *,
    orders: list[dict[str, Any]],
    proposals_by_id: dict[str, dict[str, Any]],
    position_symbols: set[str],
    settings: Settings,
    recent_actions: dict[str, set[str]],
    now: datetime,
) -> dict[str, Any]:
    symbol = str(position.get("symbol") or "")
    cost_basis = abs(_money(position.get("cost_basis")) or 0.0)
    unrealized_pl = _money(position.get("unrealized_pl")) or 0.0
    market_value = _money(position.get("market_value")) or 0.0
    proposal = _proposal_for_position(symbol, orders, proposals_by_id)
    proposal_payload = (proposal or {}).get("payload") or {}

    metrics = {
        "symbol": symbol,
        "cost_basis": cost_basis,
        "market_value": market_value,
        "unrealized_pl": unrealized_pl,
        "unrealized_pl_pct_of_debit": round((unrealized_pl / cost_basis) * 100, 2) if cost_basis else None,
        "proposal_id": (proposal or {}).get("proposal_id"),
        "strategy_type": proposal_payload.get("strategy_type"),
        "expiration": proposal_payload.get("expiration"),
        "days_held": _days_held(symbol, orders, now),
        "days_to_expiration": _days_to_expiration(proposal_payload.get("expiration"), now),
    }

    action = "hold"
    reason = "Position is within monitor thresholds."
    priority = 0

    unpaired = _unpaired_spread_alert(symbol, proposal_payload, position_symbols)
    if unpaired:
        alerts_action = "alert_unpaired_leg"
        if not _action_blocked(symbol, alerts_action, recent_actions):
            action = alerts_action
            reason = unpaired
            priority = 80

    if action == "hold" and cost_basis > 0:
        take_profit_threshold = cost_basis * settings.take_profit_pct / 100
        stop_loss_threshold = -cost_basis * settings.stop_loss_pct / 100
        if unrealized_pl >= take_profit_threshold:
            candidate = "take_profit"
            if not _action_blocked(symbol, candidate, recent_actions):
                action = candidate
                reason = (
                    f"Unrealized P&L ${unrealized_pl:.2f} reached "
                    f"{settings.take_profit_pct:.0f}% of debit (${take_profit_threshold:.2f})."
                )
                priority = 60
        elif unrealized_pl <= stop_loss_threshold:
            candidate = "stop_loss"
            if not _action_blocked(symbol, candidate, recent_actions):
                action = candidate
                reason = (
                    f"Unrealized P&L ${unrealized_pl:.2f} breached "
                    f"{settings.stop_loss_pct:.0f}% stop on debit (${abs(stop_loss_threshold):.2f})."
                )
                priority = 90

    days_held = metrics["days_held"]
    if action == "hold" and days_held is not None and days_held >= settings.time_stop_days:
        candidate = "time_stop"
        if not _action_blocked(symbol, candidate, recent_actions):
            action = candidate
            reason = f"Position held {days_held} days, exceeding {settings.time_stop_days}-day time stop."
            priority = 50

    days_to_expiration = metrics["days_to_expiration"]
    if (
        action == "hold"
        and days_to_expiration is not None
        and days_to_expiration <= settings.expiration_risk_days
    ):
        candidate = "expiration_risk"
        if not _action_blocked(symbol, candidate, recent_actions):
            action = candidate
            reason = (
                f"Expiration in {days_to_expiration} day(s), inside "
                f"{settings.expiration_risk_days}-day risk window."
            )
            priority = 70

    return {
        "symbol": symbol,
        "action": action,
        "reason": reason,
        "priority": priority,
        "metrics": metrics,
        "should_close": action in {"take_profit", "stop_loss", "time_stop", "expiration_risk"},
    }


def _summarize(decisions: list[dict[str, Any]], alerts: list[dict[str, Any]]) -> dict[str, Any]:
    close_candidates = [decision for decision in decisions if decision.get("should_close")]
    hold_count = len([decision for decision in decisions if decision.get("action") == "hold"])
    return {
        "hold_count": hold_count,
        "close_candidate_count": len(close_candidates),
        "alert_count": len(alerts) + len([d for d in decisions if d.get("action", "").startswith("alert_")]),
        "top_priority_action": _top_priority(decisions + [{"action": a.get("type"), "priority": a.get("priority", 0)} for a in alerts]),
    }


def _top_priority(items: list[dict[str, Any]]) -> str | None:
    ranked = sorted(items, key=lambda item: item.get("priority", 0), reverse=True)
    for item in ranked:
        action = item.get("action")
        if action and action != "hold":
            return str(action)
    return None


def _proposal_for_position(
    symbol: str,
    orders: list[dict[str, Any]],
    proposals_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    for order in orders:
        proposal_id = order.get("proposal_id")
        if not proposal_id:
            continue
        proposal = proposals_by_id.get(proposal_id)
        if proposal is None:
            continue
        legs = (proposal.get("payload") or {}).get("legs") or []
        leg_symbols = {str(leg.get("symbol") or "") for leg in legs}
        if symbol in leg_symbols:
            return proposal
    return None


def _unpaired_spread_alert(
    symbol: str,
    proposal_payload: dict[str, Any],
    position_symbols: set[str],
) -> str | None:
    strategy = str(proposal_payload.get("strategy_type") or "")
    if strategy not in {"bull_call_debit_spread", "bear_put_debit_spread"}:
        return None
    legs = proposal_payload.get("legs") or []
    if len(legs) != 2:
        return None
    leg_symbols = [str(leg.get("symbol") or "") for leg in legs]
    open_legs = [leg_symbol for leg_symbol in leg_symbols if leg_symbol in position_symbols]
    if len(open_legs) == 1:
        return f"Spread position missing paired leg; only {open_legs[0]} remains open."
    return None


def _drawdown_alert(account: dict[str, Any], settings: Settings) -> dict[str, Any] | None:
    equity = _money(account.get("equity") or account.get("portfolio_value"))
    last_equity = _money(account.get("last_equity"))
    if equity is None or last_equity is None or last_equity <= 0:
        return None
    drawdown_pct = ((equity - last_equity) / last_equity) * 100
    if drawdown_pct <= -settings.max_drawdown_pct:
        return {
            "type": "drawdown_halt",
            "priority": 100,
            "reason": (
                f"Account drawdown {drawdown_pct:.2f}% exceeds "
                f"{settings.max_drawdown_pct:.1f}% halt threshold."
            ),
            "metrics": {"equity": equity, "last_equity": last_equity, "drawdown_pct": round(drawdown_pct, 2)},
        }
    return None


def _days_held(symbol: str, orders: list[dict[str, Any]], now: datetime) -> int | None:
    timestamps: list[datetime] = []
    for order in orders:
        response = order.get("response") or {}
        request = order.get("request") or {}
        order_symbols = {str(request.get("symbol") or "")}
        for leg in request.get("legs") or []:
            order_symbols.add(str(leg.get("symbol") or ""))
        if symbol not in order_symbols:
            continue
        for key in ("filled_at", "updated_at", "submitted_at"):
            parsed = _parse_time(response.get(key))
            if parsed is not None:
                timestamps.append(parsed)
                break
    if not timestamps:
        return None
    earliest = min(timestamps)
    return max((now - earliest).days, 0)


def _days_to_expiration(expiration: Any, now: datetime) -> int | None:
    if not expiration:
        return None
    try:
        expiry = datetime.fromisoformat(str(expiration)).date()
    except ValueError:
        try:
            expiry = datetime.strptime(str(expiration), "%Y-%m-%d").date()
        except ValueError:
            return None
    return (expiry - now.date()).days


def _action_blocked(symbol: str, action: str, recent_actions: dict[str, set[str]]) -> bool:
    return action in recent_actions.get(symbol, set())


def _order_is_terminal(order: dict[str, Any]) -> bool:
    status = str((order.get("response") or {}).get("status") or "").lower()
    from app.storage.audit import TERMINAL_ORDER_STATUSES

    return status in TERMINAL_ORDER_STATUSES


def _money(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed
