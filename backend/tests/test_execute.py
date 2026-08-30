from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.config import Settings
from app.dependencies import get_alpaca_gateway
from app.main import app
from app.storage.audit import create_run, record_trade_proposal


def _fresh_proposal() -> dict:
    expiration = (datetime.now(tz=UTC).date() + timedelta(days=14)).isoformat()
    now = datetime.now(tz=UTC).isoformat()
    return {
        "accepted": True,
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
                "quote_timestamp": now,
            },
            {
                "side": "sell",
                "symbol": "SPY260918C00645000",
                "type": "call",
                "strike": 645.0,
                "bid": 2.45,
                "ask": 2.6,
                "quote_timestamp": now,
            },
        ],
    }


def test_execute_dry_run_in_demo_mode(monkeypatch):
    demo_settings = Settings(demo_mode=True, alpaca_paper=True)
    monkeypatch.setattr("app.routes.trades.get_settings", lambda: demo_settings)
    gateway = __import__("app.alpaca_client", fromlist=["AlpacaGateway"]).AlpacaGateway(demo_settings)

    def open_clock():
        from datetime import timedelta

        now = datetime.now(tz=UTC)
        return {
            "timestamp": now.isoformat(),
            "is_open": True,
            "next_open": now.isoformat(),
            "next_close": (now + timedelta(hours=4)).isoformat(),
            "source": "demo",
        }

    gateway.clock = open_clock
    app.dependency_overrides[get_alpaca_gateway] = lambda: gateway

    client = TestClient(app)
    run_id = create_run("trade_proposal", {"test": True})
    proposal_id = record_trade_proposal(run_id, _fresh_proposal())

    response = client.post(f"/api/trades/execute/{proposal_id}", params={"dry_run": "true"})
    assert response.status_code == 200
    body = response.json()
    assert body["dry_run"] is True
    assert body["risk_approved"] is True
    assert body["order_payload"]["order_class"] == "mleg"

    app.dependency_overrides.clear()
