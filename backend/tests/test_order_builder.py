from app.trading.order_builder import build_order_payload


def test_build_spread_order_payload():
    proposal = {
        "strategy_type": "bull_call_debit_spread",
        "legs": [
            {"side": "buy", "symbol": "SPY260918C00640000", "bid": 5.0, "ask": 5.2},
            {"side": "sell", "symbol": "SPY260918C00645000", "bid": 2.45, "ask": 2.6},
        ],
    }
    payload = build_order_payload(proposal, "FDA-TEST-SPY-001")
    assert payload["order_class"] == "mleg"
    assert payload["limit_price"] == 2.57
    assert len(payload["legs"]) == 2
    assert payload["client_order_id"] == "FDA-TEST-SPY-001"


def test_build_single_leg_order_payload():
    proposal = {
        "strategy_type": "long_call",
        "legs": [{"side": "buy", "symbol": "SPY260918C00640000", "bid": 5.0, "ask": 5.2}],
    }
    payload = build_order_payload(proposal, "FDA-TEST-SPY-002")
    assert payload["symbol"] == "SPY260918C00640000"
    assert payload["limit_price"] == 5.1
    assert payload["position_intent"] == "buy_to_open"
