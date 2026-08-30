from datetime import UTC, datetime, timedelta

import pytest

from app.config import Settings
from app.trading.risk import evaluate_risk


def _settings(**overrides) -> Settings:
    base = {
        "alpaca_paper": True,
        "max_risk_per_trade_pct": 1.5,
        "max_daily_loss_pct": 3.0,
        "max_drawdown_pct": 8.0,
        "max_open_option_trades": 5,
        "max_same_underlying_trades": 2,
        "max_total_premium_pct": 20.0,
    }
    base.update(overrides)
    return Settings(**base)


def _account(**overrides) -> dict:
    base = {
        "equity": "100000.00",
        "buying_power": "200000.00",
        "last_equity": "100500.00",
    }
    base.update(overrides)
    return base


def _clock(**overrides) -> dict:
    now = datetime.now(tz=UTC)
    base = {
        "is_open": True,
        "next_close": (now + timedelta(hours=4)).isoformat(),
    }
    base.update(overrides)
    return base


def _fresh_quote_timestamp() -> str:
    return datetime.now(tz=UTC).isoformat()


def _good_spread_proposal(**overrides) -> dict:
    expiration = (datetime.now(tz=UTC).date() + timedelta(days=14)).isoformat()
    base = {
        "underlying_symbol": "SPY",
        "strategy_type": "bull_call_debit_spread",
        "direction": "bullish",
        "expiration": expiration,
        "estimated_net_debit": 255.0,
        "max_loss": 255.0,
        "legs": [
            {
                "side": "buy",
                "symbol": "SPY260918C00640000",
                "type": "call",
                "strike": 640.0,
                "bid": 5.0,
                "ask": 5.2,
                "quote_timestamp": _fresh_quote_timestamp(),
            },
            {
                "side": "sell",
                "symbol": "SPY260918C00645000",
                "type": "call",
                "strike": 645.0,
                "bid": 2.45,
                "ask": 2.6,
                "quote_timestamp": _fresh_quote_timestamp(),
            },
        ],
    }
    base.update(overrides)
    return base


def test_reject_live_mode():
    result = evaluate_risk(
        _good_spread_proposal(),
        _account(),
        _clock(),
        [],
        _settings(alpaca_paper=False),
    )
    assert result["approved"] is False
    assert "paper_trading_required" in result["blocking_reasons"]


def test_reject_too_large_risk():
    result = evaluate_risk(
        _good_spread_proposal(max_loss=5000.0, estimated_net_debit=5000.0),
        _account(),
        _clock(),
        [],
        _settings(),
    )
    assert result["approved"] is False
    assert "max_risk_per_trade_exceeded" in result["blocking_reasons"]


def test_reject_stale_quote():
    stale = (datetime.now(tz=UTC) - timedelta(hours=2)).isoformat()
    proposal = _good_spread_proposal()
    proposal["legs"][0]["quote_timestamp"] = stale
    result = evaluate_risk(proposal, _account(), _clock(), [], _settings())
    assert result["approved"] is False
    assert "stale_option_quote" in result["blocking_reasons"]


def test_reject_wide_spread():
    proposal = _good_spread_proposal()
    proposal["legs"][0]["bid"] = 1.0
    proposal["legs"][0]["ask"] = 5.0
    result = evaluate_risk(proposal, _account(), _clock(), [], _settings())
    assert result["approved"] is False
    assert "option_spread_too_wide" in result["blocking_reasons"]


def test_reject_unsupported_strategy():
    proposal = _good_spread_proposal(strategy_type="iron_condor")
    result = evaluate_risk(proposal, _account(), _clock(), [], _settings())
    assert result["approved"] is False
    assert "unsupported_strategy" in result["blocking_reasons"]


def test_approve_known_good_debit_spread():
    result = evaluate_risk(_good_spread_proposal(), _account(), _clock(), [], _settings())
    assert result["approved"] is True
    assert result["blocking_reasons"] == []
    assert result["position_size"] == 1
    assert result["max_loss"] == 255.0


def test_reject_market_closed():
    result = evaluate_risk(
        _good_spread_proposal(),
        _account(),
        _clock(is_open=False),
        [],
        _settings(),
    )
    assert result["approved"] is False
    assert "market_not_open" in result["blocking_reasons"]
