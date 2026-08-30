from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.config import Settings

ALLOWED_STRATEGIES = {
    "bull_call_debit_spread",
    "bear_put_debit_spread",
    "long_call",
    "long_put",
}


def evaluate_risk(
    proposal: dict[str, Any],
    account: dict[str, Any],
    clock: dict[str, Any],
    positions: list[dict[str, Any]],
    settings: Settings,
) -> dict[str, Any]:
    blocking_reasons: list[str] = []
    warnings: list[str] = []

    equity = _money(account.get("equity") or account.get("portfolio_value"))
    buying_power = _money(account.get("buying_power"))
    max_loss = _money(proposal.get("max_loss"))
    premium = _money(proposal.get("estimated_net_debit")) or max_loss
    underlying = str(proposal.get("underlying_symbol") or "")
    strategy_type = str(proposal.get("strategy_type") or "")

    if not settings.alpaca_paper:
        blocking_reasons.append("paper_trading_required")
    if equity is None or equity <= 0:
        blocking_reasons.append("account_equity_unavailable")
    if buying_power is None or buying_power <= 0:
        blocking_reasons.append("buying_power_unavailable")
    if not _clock_is_open(clock):
        blocking_reasons.append("market_not_open")
    if _inside_entry_cutoff(clock):
        blocking_reasons.append("inside_end_of_day_entry_cutoff")
    if strategy_type not in ALLOWED_STRATEGIES:
        blocking_reasons.append("unsupported_strategy")
    if not _has_supported_leg_structure(proposal):
        blocking_reasons.append("unsupported_or_naked_option_structure")
    if max_loss is None or max_loss <= 0:
        blocking_reasons.append("max_loss_unavailable")

    computed_risk = {
        "equity": equity,
        "buying_power": buying_power,
        "max_loss": max_loss,
        "premium": premium,
        "max_risk_allowed": round(equity * settings.max_risk_per_trade_pct / 100, 2) if equity else None,
        "premium_deployed_limit": round(equity * settings.max_total_premium_pct / 100, 2) if equity else None,
        "open_option_trades": _open_option_trade_count(positions),
        "same_underlying_trades": _same_underlying_count(positions, underlying),
    }

    if equity and max_loss and max_loss > computed_risk["max_risk_allowed"]:
        blocking_reasons.append("max_risk_per_trade_exceeded")
    if buying_power and premium and premium > buying_power:
        blocking_reasons.append("insufficient_buying_power")
    if computed_risk["open_option_trades"] >= settings.max_open_option_trades:
        blocking_reasons.append("max_open_option_trades_exceeded")
    if computed_risk["same_underlying_trades"] >= settings.max_same_underlying_trades:
        blocking_reasons.append("max_same_underlying_exposure_exceeded")
    if equity and premium and premium > computed_risk["premium_deployed_limit"]:
        blocking_reasons.append("max_total_premium_deployed_exceeded")

    for reason in _quote_risk_reasons(proposal):
        blocking_reasons.append(reason)
    if not _expiration_is_far_enough(proposal):
        blocking_reasons.append("expiration_too_close")

    if account.get("last_equity") and equity:
        drawdown_pct = _pct_change(equity, _money(account.get("last_equity")))
        if drawdown_pct <= -settings.max_drawdown_pct:
            blocking_reasons.append("max_drawdown_exceeded")
        if drawdown_pct <= -settings.max_daily_loss_pct:
            blocking_reasons.append("max_daily_loss_exceeded")
        computed_risk["equity_change_pct"] = round(drawdown_pct, 3)
    else:
        warnings.append("daily_loss_and_drawdown_require_account_last_equity")

    position_size = 0 if blocking_reasons else 1
    return {
        "approved": not blocking_reasons,
        "blocking_reasons": sorted(set(blocking_reasons)),
        "warnings": warnings,
        "computed_risk": computed_risk,
        "position_size": position_size,
        "max_loss": max_loss,
        "timestamp": datetime.now(tz=UTC).isoformat(),
    }


def _has_supported_leg_structure(proposal: dict[str, Any]) -> bool:
    legs = proposal.get("legs") or []
    strategy_type = proposal.get("strategy_type")
    buys = [leg for leg in legs if leg.get("side") == "buy"]
    sells = [leg for leg in legs if leg.get("side") == "sell"]
    if strategy_type in {"long_call", "long_put"}:
        return len(buys) == 1 and not sells
    if strategy_type in {"bull_call_debit_spread", "bear_put_debit_spread"}:
        if len(buys) != 1 or len(sells) != 1:
            return False
        buy, sell = buys[0], sells[0]
        if buy.get("type") != sell.get("type"):
            return False
        if strategy_type == "bull_call_debit_spread":
            return buy.get("type") == "call" and _money(buy.get("strike")) < _money(sell.get("strike"))
        return buy.get("type") == "put" and _money(buy.get("strike")) > _money(sell.get("strike"))
    return False


def _quote_risk_reasons(proposal: dict[str, Any]) -> list[str]:
    reasons = []
    for leg in proposal.get("legs") or []:
        bid = _money(leg.get("bid"))
        ask = _money(leg.get("ask"))
        if bid is None or ask is None or ask <= 0:
            reasons.append("missing_option_quote")
            continue
        if _spread_pct(bid, ask) > 20:
            reasons.append("option_spread_too_wide")
        if not _quote_is_fresh(leg.get("quote_timestamp")):
            reasons.append("stale_option_quote")
    return reasons


def _expiration_is_far_enough(proposal: dict[str, Any]) -> bool:
    raw = proposal.get("expiration")
    if not raw:
        return False
    try:
        expiration = datetime.fromisoformat(str(raw)).date()
    except ValueError:
        return False
    return (expiration - datetime.now(tz=UTC).date()).days >= 7


def _clock_is_open(clock: dict[str, Any]) -> bool:
    return bool(clock.get("is_open"))


def _inside_entry_cutoff(clock: dict[str, Any]) -> bool:
    if not clock.get("is_open") or not clock.get("next_close"):
        return False
    try:
        next_close = datetime.fromisoformat(str(clock["next_close"]).replace("Z", "+00:00"))
    except ValueError:
        return False
    return next_close.astimezone(UTC) - datetime.now(tz=UTC) <= timedelta(minutes=10)


def _open_option_trade_count(positions: list[dict[str, Any]]) -> int:
    return sum(1 for position in positions if str(position.get("asset_class", "")).lower() == "us_option")


def _same_underlying_count(positions: list[dict[str, Any]], underlying: str) -> int:
    if not underlying:
        return 0
    return sum(1 for position in positions if str(position.get("symbol", "")).upper().startswith(underlying.upper()))


def _quote_is_fresh(timestamp: Any, max_age_seconds: int = 900) -> bool:
    if not timestamp:
        return False
    try:
        parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
    except ValueError:
        return False
    return (datetime.now(tz=UTC) - parsed.astimezone(UTC)).total_seconds() <= max_age_seconds


def _spread_pct(bid: float, ask: float) -> float:
    midpoint = (bid + ask) / 2
    if midpoint <= 0:
        return 100.0
    return ((ask - bid) / midpoint) * 100


def _pct_change(current: float | None, previous: float | None) -> float:
    if current is None or previous in (None, 0):
        return 0.0
    return ((current - previous) / previous) * 100


def _money(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
