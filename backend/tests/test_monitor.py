from datetime import UTC, datetime, timedelta

from app.config import Settings
from app.trading.monitor import evaluate_position, run_monitor


def _settings() -> Settings:
    return Settings(
        demo_mode=True,
        take_profit_pct=50.0,
        stop_loss_pct=50.0,
        time_stop_days=14,
        expiration_risk_days=3,
        max_drawdown_pct=8.0,
    )


def _proposal(spread: bool = False) -> dict:
    expiration = (datetime.now(tz=UTC).date() + timedelta(days=10)).isoformat()
    legs = [
        {"symbol": "SPY260918C00640000", "side": "buy"},
        {"symbol": "SPY260918C00645000", "side": "sell"},
    ]
    return {
        "proposal_id": "proposal_test",
        "payload": {
            "strategy_type": "bull_call_debit_spread" if spread else "long_call",
            "expiration": expiration,
            "legs": legs if spread else [legs[0]],
        },
    }


def test_take_profit_trigger():
    position = {
        "symbol": "SPY260918C00640000",
        "qty": "1",
        "cost_basis": "500.00",
        "market_value": "760.00",
        "unrealized_pl": "260.00",
    }
    decision = evaluate_position(
        position,
        orders=[{"proposal_id": "proposal_test", "request": {}, "response": {}}],
        proposals_by_id={"proposal_test": _proposal()},
        position_symbols={"SPY260918C00640000"},
        settings=_settings(),
        recent_actions={},
        now=datetime.now(tz=UTC),
    )
    assert decision["action"] == "take_profit"
    assert decision["should_close"] is True


def test_stop_loss_trigger():
    position = {
        "symbol": "SPY260918C00640000",
        "qty": "1",
        "cost_basis": "500.00",
        "market_value": "200.00",
        "unrealized_pl": "-300.00",
    }
    decision = evaluate_position(
        position,
        orders=[{"proposal_id": "proposal_test", "request": {}, "response": {}}],
        proposals_by_id={"proposal_test": _proposal()},
        position_symbols={"SPY260918C00640000"},
        settings=_settings(),
        recent_actions={},
        now=datetime.now(tz=UTC),
    )
    assert decision["action"] == "stop_loss"
    assert decision["should_close"] is True


def test_time_stop_trigger():
    now = datetime.now(tz=UTC)
    position = {
        "symbol": "SPY260918C00640000",
        "qty": "1",
        "cost_basis": "500.00",
        "market_value": "520.00",
        "unrealized_pl": "20.00",
    }
    old_submit = (now - timedelta(days=20)).isoformat()
    decision = evaluate_position(
        position,
        orders=[
            {
                "proposal_id": "proposal_test",
                "request": {"symbol": "SPY260918C00640000"},
                "response": {"submitted_at": old_submit},
            }
        ],
        proposals_by_id={"proposal_test": _proposal()},
        position_symbols={"SPY260918C00640000"},
        settings=_settings(),
        recent_actions={},
        now=now,
    )
    assert decision["action"] == "time_stop"


def test_expiration_risk_trigger():
    now = datetime.now(tz=UTC)
    near_expiry = (now.date() + timedelta(days=2)).isoformat()
    position = {
        "symbol": "SPY260918C00640000",
        "qty": "1",
        "cost_basis": "500.00",
        "market_value": "520.00",
        "unrealized_pl": "20.00",
    }
    proposal = _proposal()
    proposal["payload"]["expiration"] = near_expiry
    decision = evaluate_position(
        position,
        orders=[{"proposal_id": "proposal_test", "request": {}, "response": {}}],
        proposals_by_id={"proposal_test": proposal},
        position_symbols={"SPY260918C00640000"},
        settings=_settings(),
        recent_actions={},
        now=now,
    )
    assert decision["action"] == "expiration_risk"


def test_unpaired_spread_alert():
    position = {
        "symbol": "SPY260918C00640000",
        "qty": "1",
        "cost_basis": "500.00",
        "market_value": "520.00",
        "unrealized_pl": "20.00",
    }
    decision = evaluate_position(
        position,
        orders=[{"proposal_id": "proposal_test", "request": {}, "response": {}}],
        proposals_by_id={"proposal_test": _proposal(spread=True)},
        position_symbols={"SPY260918C00640000"},
        settings=_settings(),
        recent_actions={},
        now=datetime.now(tz=UTC),
    )
    assert decision["action"] == "alert_unpaired_leg"


def test_duplicate_action_is_blocked():
    position = {
        "symbol": "SPY260918C00640000",
        "qty": "1",
        "cost_basis": "500.00",
        "market_value": "760.00",
        "unrealized_pl": "260.00",
    }
    decision = evaluate_position(
        position,
        orders=[{"proposal_id": "proposal_test", "request": {}, "response": {}}],
        proposals_by_id={"proposal_test": _proposal()},
        position_symbols={"SPY260918C00640000"},
        settings=_settings(),
        recent_actions={"SPY260918C00640000": {"take_profit"}},
        now=datetime.now(tz=UTC),
    )
    assert decision["action"] == "hold"


def test_drawdown_alert_in_monitor_run():
    account = {
        "equity": "90000",
        "last_equity": "100000",
        "buying_power": "180000",
        "portfolio_value": "90000",
    }
    result = run_monitor(account, [], [], {}, _settings())
    assert result["alerts"]
    assert result["alerts"][0]["type"] == "drawdown_halt"
