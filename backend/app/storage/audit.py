from __future__ import annotations

from datetime import UTC, datetime
import json
from typing import Any
from uuid import uuid4

from app.db import connect


def now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def new_run_id(prefix: str = "run") -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def new_proposal_id() -> str:
    return f"proposal_{uuid4().hex[:12]}"


def new_order_id() -> str:
    return f"order_{uuid4().hex[:12]}"


def client_order_id(run_id: str, symbol: str, timestamp: str | None = None) -> str:
    safe_symbol = "".join(char for char in symbol.upper() if char.isalnum())
    raw_timestamp = timestamp or now_iso()
    safe_timestamp = "".join(char for char in raw_timestamp if char.isdigit())[:14]
    return f"FDA-{run_id}-{safe_symbol}-{safe_timestamp}"[:48]


def create_run(run_type: str, summary: dict[str, Any] | None = None) -> str:
    run_id = new_run_id(run_type)
    timestamp = now_iso()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO system_runs (run_id, run_type, status, started_at, summary_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, run_type, "running", timestamp, _json(summary or {})),
        )
    return run_id


def complete_run(run_id: str, summary: dict[str, Any] | None = None) -> None:
    with connect() as connection:
        connection.execute(
            """
            UPDATE system_runs
            SET status = ?, completed_at = ?, summary_json = ?
            WHERE run_id = ?
            """,
            ("completed", now_iso(), _json(summary or {}), run_id),
        )


def record_market_snapshot(run_id: str, symbols: list[str], payload: dict[str, Any]) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO market_snapshots (run_id, symbols_json, payload_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, _json(symbols), _json(payload), now_iso()),
        )


def record_option_chain(run_id: str, symbol: str, payload: dict[str, Any]) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO option_chains (run_id, underlying_symbol, payload_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, symbol, _json(payload), now_iso()),
        )


def record_trade_proposal(
    run_id: str,
    payload: dict[str, Any],
    proposal_id: str | None = None,
) -> str:
    resolved_proposal_id = proposal_id or new_proposal_id()
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO trade_proposals (proposal_id, run_id, payload_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (resolved_proposal_id, run_id, _json(payload), now_iso()),
        )
    return resolved_proposal_id


def record_risk_check(
    run_id: str,
    approved: bool,
    payload: dict[str, Any],
    proposal_id: str | None = None,
) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO risk_checks (run_id, proposal_id, approved, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, proposal_id, int(approved), _json(payload), now_iso()),
        )


def record_order(
    run_id: str,
    client_order_id_value: str,
    request_payload: dict[str, Any],
    response_payload: dict[str, Any],
    order_id: str | None = None,
    proposal_id: str | None = None,
) -> str:
    resolved_order_id = order_id or str(response_payload.get("id") or new_order_id())
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO orders (
                order_id, run_id, proposal_id, client_order_id,
                request_json, response_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                resolved_order_id,
                run_id,
                proposal_id,
                client_order_id_value,
                _json(request_payload),
                _json(response_payload),
                now_iso(),
            ),
        )
    return resolved_order_id


def record_position_snapshot(run_id: str, payload: dict[str, Any] | list[dict[str, Any]]) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO position_snapshots (run_id, payload_json, created_at)
            VALUES (?, ?, ?)
            """,
            (run_id, _json(payload), now_iso()),
        )


def record_agent_event(
    event_type: str,
    payload: dict[str, Any],
    run_id: str | None = None,
) -> None:
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO agent_events (run_id, event_type, payload_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, event_type, _json(payload), now_iso()),
        )


def list_runs(limit: int = 50) -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT run_id, run_type, status, started_at, completed_at, summary_json
            FROM system_runs
            ORDER BY started_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_run_from_row(row) for row in rows]


def get_run_detail(run_id: str) -> dict[str, Any] | None:
    with connect() as connection:
        run = connection.execute(
            """
            SELECT run_id, run_type, status, started_at, completed_at, summary_json
            FROM system_runs
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()
        if run is None:
            return None

        return {
            **_run_from_row(run),
            "market_snapshots": _select_payload_rows(
                connection,
                "SELECT id, symbols_json, payload_json, created_at FROM market_snapshots WHERE run_id = ?",
                run_id,
            ),
            "option_chains": _select_payload_rows(
                connection,
                "SELECT id, underlying_symbol, payload_json, created_at FROM option_chains WHERE run_id = ?",
                run_id,
            ),
            "trade_proposals": _select_payload_rows(
                connection,
                "SELECT proposal_id, payload_json, created_at FROM trade_proposals WHERE run_id = ?",
                run_id,
            ),
            "risk_checks": _select_payload_rows(
                connection,
                "SELECT id, proposal_id, approved, payload_json, created_at FROM risk_checks WHERE run_id = ?",
                run_id,
            ),
            "orders": _select_payload_rows(
                connection,
                "SELECT order_id, proposal_id, client_order_id, request_json, response_json, created_at FROM orders WHERE run_id = ?",
                run_id,
            ),
            "position_snapshots": _select_payload_rows(
                connection,
                "SELECT id, payload_json, created_at FROM position_snapshots WHERE run_id = ?",
                run_id,
            ),
            "agent_events": _select_payload_rows(
                connection,
                "SELECT id, event_type, payload_json, created_at FROM agent_events WHERE run_id = ?",
                run_id,
            ),
        }


TERMINAL_ORDER_STATUSES = frozenset(
    {"filled", "canceled", "cancelled", "expired", "rejected", "replaced", "done_for_day"}
)


def get_order(order_id: str) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT order_id, run_id, proposal_id, client_order_id,
                   request_json, response_json, created_at
            FROM orders
            WHERE order_id = ?
            """,
            (order_id,),
        ).fetchone()
    if row is None:
        return None
    return _decode_row(row)


def list_orders(limit: int = 100) -> list[dict[str, Any]]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT order_id, run_id, proposal_id, client_order_id,
                   request_json, response_json, created_at
            FROM orders
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_decode_row(row) for row in rows]


def list_orders_needing_sync(limit: int = 50) -> list[dict[str, Any]]:
    orders = list_orders(limit=limit)
    return [
        order
        for order in orders
        if str((order.get("response") or {}).get("status", "")).lower() not in TERMINAL_ORDER_STATUSES
    ]


def update_order_response(order_id: str, response_payload: dict[str, Any]) -> None:
    with connect() as connection:
        connection.execute(
            """
            UPDATE orders
            SET response_json = ?
            WHERE order_id = ?
            """,
            (_json(response_payload), order_id),
        )


def list_agent_events(
    event_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    query = """
        SELECT id, run_id, event_type, payload_json, created_at
        FROM agent_events
    """
    params: list[Any] = []
    if event_type:
        query += " WHERE event_type = ?"
        params.append(event_type)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with connect() as connection:
        rows = connection.execute(query, params).fetchall()
    return [_decode_row(row) for row in rows]


def has_recent_monitor_action(
    symbol: str,
    action: str,
    cooldown_hours: int,
) -> bool:
    from datetime import UTC, datetime, timedelta

    cutoff = datetime.now(tz=UTC) - timedelta(hours=cooldown_hours)
    events = list_agent_events(event_type="monitor_action", limit=200)
    for event in events:
        payload = event.get("payload") or {}
        if payload.get("symbol") != symbol or payload.get("action") != action:
            continue
        created_at = event.get("created_at")
        if not created_at:
            continue
        try:
            event_time = datetime.fromisoformat(str(created_at))
        except ValueError:
            continue
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=UTC)
        if event_time >= cutoff:
            return True
    return False


def get_proposal(proposal_id: str) -> dict[str, Any] | None:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT proposal_id, run_id, payload_json, created_at
            FROM trade_proposals
            WHERE proposal_id = ?
            """,
            (proposal_id,),
        ).fetchone()
    if row is None:
        return None
    return _decode_row(row)


def _select_payload_rows(connection, query: str, run_id: str) -> list[dict[str, Any]]:
    return [_decode_row(row) for row in connection.execute(query, (run_id,)).fetchall()]


def _run_from_row(row) -> dict[str, Any]:
    return {
        "run_id": row["run_id"],
        "run_type": row["run_type"],
        "status": row["status"],
        "started_at": row["started_at"],
        "completed_at": row["completed_at"],
        "summary": json.loads(row["summary_json"]),
    }


def _decode_row(row) -> dict[str, Any]:
    decoded = dict(row)
    for key, value in list(decoded.items()):
        if key.endswith("_json") and isinstance(value, str):
            decoded[key.removesuffix("_json")] = json.loads(value)
            del decoded[key]
    return decoded


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)
