from uuid import uuid4

from app.trading.order_sync import classify_order_status, sync_open_orders, sync_order
from app.storage.audit import create_run, get_order, record_order


def test_classify_filled_order():
    summary = classify_order_status({"status": "filled", "qty": "2", "filled_qty": "2"})
    assert summary["is_filled"] is True
    assert summary["is_terminal"] is True
    assert summary["is_partial"] is False


def test_classify_partial_fill():
    summary = classify_order_status({"status": "partially_filled", "qty": "2", "filled_qty": "1"})
    assert summary["is_partial"] is True
    assert summary["is_terminal"] is False


def test_classify_rejected_order():
    summary = classify_order_status({"status": "rejected", "qty": "1", "filled_qty": "0"})
    assert summary["is_rejected"] is True
    assert summary["is_terminal"] is True


def test_sync_order_updates_stored_response(monkeypatch):
    run_id = create_run("order_sync_test")
    order_id = str(uuid4())
    record_order(
        run_id,
        "FDA-TEST-SPY-001",
        {"symbol": "SPY260918C00600000", "qty": 1},
        {"id": order_id, "status": "accepted", "qty": "1", "filled_qty": "0"},
        order_id=order_id,
    )

    class FakeGateway:
        def get_order(self, requested_id: str):
            assert requested_id == order_id
            return {
                "id": order_id,
                "status": "partially_filled",
                "qty": "2",
                "filled_qty": "1",
            }

    result = sync_order(FakeGateway(), order_id)
    assert result["is_partial"] is True
    assert result["status"] == "partially_filled"

    stored = get_order(order_id)
    assert stored["response"]["status"] == "partially_filled"
    assert stored["response"]["filled_qty"] == "1"


def test_sync_open_orders_skips_non_alpaca_ids():
    run_id = create_run("order_sync_skip_test")
    order_id = f"demo-order-{uuid4().hex[:8]}"
    record_order(
        run_id,
        "FDA-TEST-SKIP-001",
        {"symbol": "SPY260918C00600000", "qty": 1},
        {"id": order_id, "status": "accepted", "qty": "1"},
        order_id=order_id,
    )

    class FakeGateway:
        def get_order(self, requested_id: str):
            raise AssertionError(f"unexpected sync for {requested_id}")

    synced = sync_open_orders(FakeGateway(), limit=100)
    assert all(item.get("order_id") != order_id for item in synced)
