from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def rank_candidates(snapshots: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = [_score_symbol(symbol, snapshot) for symbol, snapshot in snapshots.items()]
    candidates.sort(key=lambda candidate: candidate["best_score"], reverse=True)
    return candidates


def no_trade_candidate(reason: str) -> dict[str, Any]:
    return {
        "symbol": "NO_TRADE",
        "direction": "none",
        "best_score": 0.0,
        "bullish_score": 0.0,
        "bearish_score": 0.0,
        "volatility_score": 0.0,
        "features": {},
        "reason_codes": [reason],
    }


def _score_symbol(symbol: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    trade_price = _number_at(snapshot, ["latest_trade", "price"]) or _number_at(snapshot, ["latest_trade", "p"])
    quote_bid = _number_at(snapshot, ["latest_quote", "bid_price"]) or _number_at(snapshot, ["latest_quote", "bp"])
    quote_ask = _number_at(snapshot, ["latest_quote", "ask_price"]) or _number_at(snapshot, ["latest_quote", "ap"])
    day_open = _number_at(snapshot, ["daily_bar", "open"]) or _number_at(snapshot, ["daily_bar", "o"])
    day_close = _number_at(snapshot, ["daily_bar", "close"]) or _number_at(snapshot, ["daily_bar", "c"]) or trade_price
    minute_volume = _number_at(snapshot, ["minute_bar", "volume"]) or _number_at(snapshot, ["minute_bar", "v"])

    intraday_return = _pct_change(day_close, day_open)
    spread_pct = _spread_pct(quote_bid, quote_ask)
    volume_score = min((minute_volume or 0) / 100_000, 3.0) / 3.0
    quote_fresh = _quote_is_fresh(snapshot)

    bullish_score = _clamp(50 + intraday_return * 8 + volume_score * 15 - spread_pct * 0.5)
    bearish_score = _clamp(50 - intraday_return * 8 + volume_score * 15 - spread_pct * 0.5)
    volatility_score = _clamp(abs(intraday_return) * 10 + volume_score * 30)

    if not quote_fresh:
        bullish_score *= 0.6
        bearish_score *= 0.6
        volatility_score *= 0.6

    direction = "bullish" if bullish_score >= bearish_score else "bearish"
    best_score = max(bullish_score, bearish_score)

    reason_codes = []
    if intraday_return > 0.25:
        reason_codes.append("positive_intraday_momentum")
    if intraday_return < -0.25:
        reason_codes.append("negative_intraday_momentum")
    if volume_score > 0.5:
        reason_codes.append("liquid_recent_volume")
    if spread_pct <= 0.5:
        reason_codes.append("tight_quote_spread")
    if not quote_fresh:
        reason_codes.append("stale_or_missing_quote_timestamp")
    if best_score < 55:
        reason_codes.append("weak_directional_edge")

    return {
        "symbol": symbol,
        "direction": direction if best_score >= 55 else "none",
        "best_score": round(best_score, 2),
        "bullish_score": round(bullish_score, 2),
        "bearish_score": round(bearish_score, 2),
        "volatility_score": round(volatility_score, 2),
        "features": {
            "intraday_return_pct": round(intraday_return, 3),
            "bid_ask_spread_pct": round(spread_pct, 3),
            "minute_volume": minute_volume,
            "quote_fresh": quote_fresh,
            "last_price": trade_price,
        },
        "reason_codes": reason_codes,
    }


def _number_at(payload: dict[str, Any], path: list[str]) -> float | None:
    value: Any = payload
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pct_change(current: float | None, previous: float | None) -> float:
    if current is None or previous in (None, 0):
        return 0.0
    return ((current - previous) / previous) * 100


def _spread_pct(bid: float | None, ask: float | None) -> float:
    if bid is None or ask is None or bid <= 0 or ask <= 0:
        return 100.0
    midpoint = (bid + ask) / 2
    return ((ask - bid) / midpoint) * 100


def _quote_is_fresh(snapshot: dict[str, Any]) -> bool:
    timestamp = _value_at(snapshot, ["latest_quote", "timestamp"]) or _value_at(snapshot, ["latest_quote", "t"])
    if not timestamp:
        return False
    try:
        parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
    except ValueError:
        return False
    return (datetime.now(tz=UTC) - parsed.astimezone(UTC)).total_seconds() <= 300


def _value_at(payload: dict[str, Any], path: list[str]) -> Any:
    value: Any = payload
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))
