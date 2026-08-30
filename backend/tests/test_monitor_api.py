from uuid import uuid4

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.config import Settings
from app.dependencies import get_alpaca_gateway
from app.main import app
from app.storage.audit import create_run, record_order, record_trade_proposal


def test_monitor_run_in_demo_mode(monkeypatch):
    demo_settings = Settings(demo_mode=True, alpaca_paper=True)
    monkeypatch.setattr("app.routes.monitor.get_settings", lambda: demo_settings)
    gateway = __import__("app.alpaca_client", fromlist=["AlpacaGateway"]).AlpacaGateway(demo_settings)
    app.dependency_overrides[get_alpaca_gateway] = lambda: gateway

    client = TestClient(app)
    response = client.post("/api/monitor/run", params={"sync_orders": "false"})
    assert response.status_code == 200
    body = response.json()
    assert body["position_count"] >= 1
    assert body["summary"]["hold_count"] >= 0
    assert "decisions" in body

    app.dependency_overrides.clear()


def test_order_sync_endpoint(monkeypatch):
    demo_settings = Settings(demo_mode=True, alpaca_paper=True)
    gateway = __import__("app.alpaca_client", fromlist=["AlpacaGateway"]).AlpacaGateway(demo_settings)
    app.dependency_overrides[get_alpaca_gateway] = lambda: gateway

    run_id = create_run("trade_execution")
    proposal_id = record_trade_proposal(
        run_id,
        {
            "accepted": True,
            "underlying_symbol": "SPY",
            "strategy_type": "long_call",
            "legs": [{"symbol": "SPY260918C00640000", "side": "buy", "bid": 5.0, "ask": 5.2}],
        },
    )
    order_id = f"demo-order-{uuid4().hex[:8]}"
    record_order(
        run_id,
        "FDA-TEST-SYNC-001",
        {"symbol": "SPY260918C00640000", "qty": 1},
        {"id": order_id, "status": "accepted", "qty": "1"},
        order_id=order_id,
        proposal_id=proposal_id,
    )

    client = TestClient(app)
    sync_response = client.post("/api/trades/sync")
    assert sync_response.status_code == 200
    synced = sync_response.json()["synced"]
    assert any(item["order_id"] == order_id for item in synced)

    status_response = client.get(f"/api/trades/orders/{order_id}/status", params={"refresh": "true"})
    assert status_response.status_code == 200
    assert status_response.json()["stored"]["order_id"] == order_id

    app.dependency_overrides.clear()


def test_build_close_order_payload():
    from app.trading.order_builder import build_close_order_payload

    payload = build_close_order_payload(
        {"symbol": "SPY260918C00640000", "qty": "1", "market_value": "540.00"},
        "FDA-CLOSE-TEST",
    )
    assert payload["side"] == "sell"
    assert payload["position_intent"] == "sell_to_close"
    assert payload["limit_price"] == 5.4
