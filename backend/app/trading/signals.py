from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def rank_candidates(
    snapshots: dict[str, Any],
    historical_bars: dict[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    bars_by_symbol = historical_bars or {}
    candidates = [
        _score_symbol(symbol, snapshot, bars_by_symbol.get(symbol, []))
        for symbol, snapshot in snapshots.items()
    ]
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


def _score_symbol(symbol: str, snapshot: dict[str, Any], bars: list[dict[str, Any]]) -> dict[str, Any]:
    trade_price = _number_at(snapshot, ["latest_trade", "price"]) or _number_at(snapshot, ["latest_trade", "p"])
    quote_bid = _number_at(snapshot, ["latest_quote", "bid_price"]) or _number_at(snapshot, ["latest_quote", "bp"])
    quote_ask = _number_at(snapshot, ["latest_quote", "ask_price"]) or _number_at(snapshot, ["latest_quote", "ap"])
    day_open = _number_at(snapshot, ["daily_bar", "open"]) or _number_at(snapshot, ["daily_bar", "o"])
    day_close = _number_at(snapshot, ["daily_bar", "close"]) or _number_at(snapshot, ["daily_bar", "c"]) or trade_price
    minute_volume = _number_at(snapshot, ["minute_bar", "volume"]) or _number_at(snapshot, ["minute_bar", "v"])

    intraday_return = _pct_change(day_close, day_open)
    one_day_return = _bar_return(bars, 1)
    five_day_return = _bar_return(bars, 5)
    ma20_slope = _ma_slope(bars, 20)
    volume_ratio = _volume_ratio(bars)
    volatility_proxy = _volatility_proxy(bars)
    spread_pct = _spread_pct(quote_bid, quote_ask)
    volume_score = min(max(volume_ratio, (minute_volume or 0) / 100_000), 3.0) / 3.0
    quote_fresh = _quote_is_fresh(snapshot)

    bullish_score = _clamp(
        50
        + intraday_return * 5
        + one_day_return * 6
        + five_day_return * 3
        + ma20_slope * 4
        + volume_score * 15
        - spread_pct * 0.5
        - volatility_proxy * 0.75
    )
    bearish_score = _clamp(
        50
        - intraday_return * 5
        - one_day_return * 6
        - five_day_return * 3
        - ma20_slope * 4
        + volume_score * 15
        - spread_pct * 0.5
        - volatility_proxy * 0.75
    )
    volatility_score = _clamp(abs(intraday_return) * 10 + volatility_proxy * 8 + volume_score * 20)

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
    if one_day_return > 0.25:
        reason_codes.append("positive_1_day_return")
    if one_day_return < -0.25:
        reason_codes.append("negative_1_day_return")
    if five_day_return > 1.0:
        reason_codes.append("positive_5_day_trend")
    if five_day_return < -1.0:
        reason_codes.append("negative_5_day_trend")
    if ma20_slope > 0:
        reason_codes.append("rising_20_day_average")
    if ma20_slope < 0:
        reason_codes.append("falling_20_day_average")
    if volatility_proxy > 2.5:
        reason_codes.append("elevated_realized_volatility")
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
            "one_day_return_pct": round(one_day_return, 3),
            "five_day_return_pct": round(five_day_return, 3),
            "volume_ratio": round(volume_ratio, 3),
            "ma20_slope_pct": round(ma20_slope, 3),
            "volatility_proxy_pct": round(volatility_proxy, 3),
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


def _bar_return(bars: list[dict[str, Any]], lookback_days: int) -> float:
    closes = [_number_at(bar, ["close"]) or _number_at(bar, ["c"]) for bar in bars]
    closes = [close for close in closes if close is not None]
    if len(closes) <= lookback_days:
        return 0.0
    return _pct_change(closes[-1], closes[-1 - lookback_days])


def _ma_slope(bars: list[dict[str, Any]], window: int) -> float:
    closes = [_number_at(bar, ["close"]) or _number_at(bar, ["c"]) for bar in bars]
    closes = [close for close in closes if close is not None]
    if len(closes) < window + 1:
        return 0.0
    current = sum(closes[-window:]) / window
    previous = sum(closes[-window - 1 : -1]) / window
    return _pct_change(current, previous)


def _volume_ratio(bars: list[dict[str, Any]]) -> float:
    volumes = [_number_at(bar, ["volume"]) or _number_at(bar, ["v"]) for bar in bars]
    volumes = [volume for volume in volumes if volume is not None]
    if len(volumes) < 2:
        return 0.0
    average = sum(volumes[:-1]) / len(volumes[:-1])
    if average <= 0:
        return 0.0
    return volumes[-1] / average


def _volatility_proxy(bars: list[dict[str, Any]]) -> float:
    highs = [_number_at(bar, ["high"]) or _number_at(bar, ["h"]) for bar in bars]
    lows = [_number_at(bar, ["low"]) or _number_at(bar, ["l"]) for bar in bars]
    closes = [_number_at(bar, ["close"]) or _number_at(bar, ["c"]) for bar in bars]
    ranges = []
    for high, low, close in zip(highs[-14:], lows[-14:], closes[-14:], strict=False):
        if high is None or low is None or close in (None, 0):
            continue
        ranges.append(((high - low) / close) * 100)
    if not ranges:
        return 0.0
    return sum(ranges) / len(ranges)


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
