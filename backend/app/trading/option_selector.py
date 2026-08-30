from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any


def select_debit_spread(
    symbol: str,
    direction: str,
    contracts_payload: dict[str, Any],
    chain_payload: dict[str, Any],
    max_debit: float = 1500.0,
    allow_single_leg_fallback: bool = True,
    max_quote_age_seconds: int = 900,
    min_open_interest: int = 50,
) -> dict[str, Any]:
    option_type = "call" if direction == "bullish" else "put"
    strategy_type = "bull_call_debit_spread" if direction == "bullish" else "bear_put_debit_spread"
    contracts = _normalize_contracts(contracts_payload, chain_payload)
    candidates = [
        contract
        for contract in contracts
        if contract["type"] == option_type
        and contract["tradable"]
        and contract["strike"] is not None
        and 7 <= contract["days_to_expiration"] <= 30
        and contract["bid"] is not None
        and contract["ask"] is not None
        and contract["ask"] > 0
        and contract["bid"] >= 0
        and _spread_pct(contract["bid"], contract["ask"]) <= 20
        and _quote_is_fresh(contract["quote_timestamp"], max_quote_age_seconds)
        and _passes_open_interest(contract["open_interest"], min_open_interest)
    ]
    candidates.sort(key=lambda contract: (contract["expiration"], _moneyness_rank(contract, option_type)))

    for expiration in sorted({contract["expiration"] for contract in candidates}):
        expiration_contracts = [contract for contract in candidates if contract["expiration"] == expiration]
        pair = _select_call_pair(expiration_contracts) if option_type == "call" else _select_put_pair(expiration_contracts)
        if pair is None:
            continue

        long_leg, short_leg = pair
        net_debit = round((long_leg["ask"] - short_leg["bid"]) * 100, 2)
        width = abs(short_leg["strike"] - long_leg["strike"]) * 100
        if net_debit <= 0 or net_debit > max_debit or net_debit >= width:
            continue

        max_profit = round(width - net_debit, 2)
        break_even = (
            round(long_leg["strike"] + net_debit / 100, 2)
            if option_type == "call"
            else round(long_leg["strike"] - net_debit / 100, 2)
        )
        return {
            "accepted": True,
            "underlying_symbol": symbol,
            "strategy_type": strategy_type,
            "direction": direction,
            "expiration": expiration,
            "legs": [
                _proposal_leg(long_leg, "buy"),
                _proposal_leg(short_leg, "sell"),
            ],
            "estimated_net_debit": net_debit,
            "max_loss": net_debit,
            "max_profit": max_profit,
            "break_even": break_even,
            "selection_reason": [
                "expiration_between_7_and_30_days",
                "tradable_contracts",
                "fresh_option_quotes",
                "open_interest_filter_passed",
                "defined_risk_debit_spread",
                "net_debit_within_budget",
            ],
        }

    if allow_single_leg_fallback:
        fallback = _select_single_leg(
            symbol=symbol,
            direction=direction,
            option_type=option_type,
            contracts=candidates,
            max_debit=max_debit,
        )
        if fallback is not None:
            return fallback

    return {
        "accepted": False,
        "underlying_symbol": symbol,
        "strategy_type": strategy_type,
        "direction": direction,
        "rejection_reasons": [
            "no_valid_debit_spread_found",
            "check_expiration_liquidity_quote_width_or_debit_budget",
        ],
    }


def _normalize_contracts(
    contracts_payload: dict[str, Any],
    chain_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    chain_by_symbol = _chain_by_symbol(chain_payload)
    raw_contracts = contracts_payload.get("option_contracts") or contracts_payload.get("contracts") or []
    normalized = []
    for contract in raw_contracts:
        contract_symbol = contract.get("symbol")
        if not contract_symbol:
            continue
        snapshot = chain_by_symbol.get(contract_symbol, {})
        quote = snapshot.get("latest_quote", snapshot)
        expiration = str(contract.get("expiration_date") or snapshot.get("expiration") or "")
        normalized.append(
            {
                "symbol": contract_symbol,
                "type": str(contract.get("type") or snapshot.get("type") or "").lower(),
                "strike": _float(contract.get("strike_price") or snapshot.get("strike")),
                "expiration": expiration,
                "days_to_expiration": _days_to_expiration(expiration),
                "tradable": bool(contract.get("tradable", snapshot.get("tradable", False))),
                "bid": _float(quote.get("bid_price") or quote.get("bid")),
                "ask": _float(quote.get("ask_price") or quote.get("ask")),
                "delta": _float((snapshot.get("greeks") or {}).get("delta") or snapshot.get("delta")),
                "open_interest": _float(contract.get("open_interest") or snapshot.get("open_interest")),
                "quote_timestamp": quote.get("timestamp") or quote.get("t") or snapshot.get("quote_timestamp"),
            }
        )
    return normalized


def _chain_by_symbol(chain_payload: dict[str, Any]) -> dict[str, Any]:
    contracts = chain_payload.get("contracts")
    if isinstance(contracts, list):
        return {contract["symbol"]: contract for contract in contracts if contract.get("symbol")}
    return {
        symbol: snapshot
        for symbol, snapshot in chain_payload.items()
        if isinstance(snapshot, dict) and symbol != "source"
    }


def _select_call_pair(contracts: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    ascending = sorted(contracts, key=lambda contract: contract["strike"])
    for index, long_leg in enumerate(ascending):
        for short_leg in ascending[index + 1 :]:
            if short_leg["strike"] > long_leg["strike"]:
                return long_leg, short_leg
    return None


def _select_put_pair(contracts: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    descending = sorted(contracts, key=lambda contract: contract["strike"], reverse=True)
    for index, long_leg in enumerate(descending):
        for short_leg in descending[index + 1 :]:
            if short_leg["strike"] < long_leg["strike"]:
                return long_leg, short_leg
    return None


def _select_single_leg(
    symbol: str,
    direction: str,
    option_type: str,
    contracts: list[dict[str, Any]],
    max_debit: float,
) -> dict[str, Any] | None:
    strategy_type = "long_call" if direction == "bullish" else "long_put"
    for contract in sorted(contracts, key=lambda item: (item["expiration"], _moneyness_rank(item, option_type))):
        net_debit = round(contract["ask"] * 100, 2)
        if net_debit <= 0 or net_debit > max_debit:
            continue
        break_even = (
            round(contract["strike"] + net_debit / 100, 2)
            if option_type == "call"
            else round(contract["strike"] - net_debit / 100, 2)
        )
        return {
            "accepted": True,
            "underlying_symbol": symbol,
            "strategy_type": strategy_type,
            "direction": direction,
            "expiration": contract["expiration"],
            "legs": [_proposal_leg(contract, "buy")],
            "estimated_net_debit": net_debit,
            "max_loss": net_debit,
            "max_profit": None,
            "break_even": break_even,
            "selection_reason": [
                "single_leg_fallback",
                "expiration_between_7_and_30_days",
                "tradable_contract",
                "fresh_option_quote",
                "net_debit_within_budget",
            ],
        }
    return None


def _proposal_leg(contract: dict[str, Any], side: str) -> dict[str, Any]:
    return {
        "side": side,
        "symbol": contract["symbol"],
        "type": contract["type"],
        "strike": contract["strike"],
        "bid": contract["bid"],
        "ask": contract["ask"],
        "delta": contract["delta"],
        "open_interest": contract["open_interest"],
        "quote_timestamp": contract["quote_timestamp"],
    }


def _spread_pct(bid: float, ask: float) -> float:
    midpoint = (bid + ask) / 2
    if midpoint <= 0:
        return 100.0
    return ((ask - bid) / midpoint) * 100


def _passes_open_interest(open_interest: float | None, minimum: int) -> bool:
    return open_interest is None or open_interest >= minimum


def _quote_is_fresh(timestamp: Any, max_age_seconds: int) -> bool:
    if not timestamp:
        return False
    try:
        parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
    except ValueError:
        return False
    return (datetime.now(tz=UTC) - parsed.astimezone(UTC)).total_seconds() <= max_age_seconds


def _moneyness_rank(contract: dict[str, Any], option_type: str) -> float:
    delta = contract.get("delta")
    if delta is not None:
        target = 0.5 if option_type == "call" else -0.5
        return abs(delta - target)
    return abs(contract["strike"] or 0)


def _days_to_expiration(expiration: str) -> int:
    try:
        expiration_date = date.fromisoformat(expiration)
    except ValueError:
        return 9999
    return (expiration_date - datetime.now(tz=UTC).date()).days


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
