"""Run a full live paper trading cycle: scan -> proposal -> review -> risk -> execute."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

BASE = "http://127.0.0.1:8000"


def get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=120) as response:
        return json.loads(response.read())


def post(path: str, body: dict | None = None, params: dict | None = None) -> dict:
    url = BASE + path
    if params:
        url += "?" + "&".join(f"{key}={value}" for key, value in params.items())
    data = None
    headers: dict[str, str] = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        print("HTTP_ERROR", exc.code, exc.read().decode()[:3000])
        raise


def main() -> None:
    print("=" * 60)
    print("FLIGHTDECK ALPHA — LIVE PAPER RUN")
    print("=" * 60)

    clock = get("/api/clock")
    print("Market open:", clock.get("is_open"), "|", clock.get("timestamp"))
    if not clock.get("is_open"):
        print("ABORT: market closed")
        raise SystemExit(1)

    account = get("/api/account")
    print(
        "Equity:", account.get("equity"),
        "BP:", account.get("buying_power"),
        "Status:", account.get("status"),
    )

    print("\n--- SCAN ---")
    scan = post("/api/scan", {"limit": 5})
    print("run_id:", scan["run_id"])
    candidates = scan["candidates"]
    for index, candidate in enumerate(candidates[:5]):
        reasons = (candidate.get("reason_codes") or [])[:3]
        print(
            f"  {index + 1}. {candidate['symbol']:6} "
            f"{candidate['direction']:8} score={candidate.get('best_score')} reasons={reasons}"
        )

    pick = None
    for candidate in candidates:
        if candidate.get("direction") in {"bullish", "bearish"} and candidate.get("symbol") != "NO_TRADE":
            pick = candidate
            break
    if pick is None:
        print("No directional candidate; using NVDA bullish fallback")
        pick = {"symbol": "NVDA", "direction": "bullish"}

    symbol = pick["symbol"]
    direction = pick["direction"]
    print(f"\nSelected: {symbol} {direction}")

    print("\n--- PROPOSAL ---")
    proposal = post("/api/proposals", {"symbol": symbol, "direction": direction, "max_debit": 1500})
    print("accepted:", proposal.get("accepted"))
    if not proposal.get("accepted"):
        print("rejection:", proposal.get("rejection_reasons"))
        raise SystemExit(1)

    proposal_id = proposal["proposal_id"]
    print("proposal_id:", proposal_id)
    print("strategy:", proposal.get("strategy_type"))
    print("expiration:", proposal.get("expiration"))
    print(
        "debit:", proposal.get("estimated_net_debit"),
        "max_loss:", proposal.get("max_loss"),
        "max_profit:", proposal.get("max_profit"),
    )
    for leg in proposal.get("legs", []):
        print(
            f"  {leg['side']:4} {leg['symbol']} strike={leg['strike']} "
            f"delta={leg.get('delta')} bid={leg['bid']} ask={leg['ask']}"
        )

    print("\n--- AGENT REVIEW ---")
    review = post("/api/proposals/review", {"proposal_id": proposal_id, "market_candidate": pick})
    print("source:", review.get("source"))
    print("critic_passed:", review.get("critic", {}).get("passed"))
    thesis = (review.get("analyst", {}) or {}).get("thesis") or ""
    print("thesis:", thesis[:250])
    blocking = (review.get("critic", {}) or {}).get("blocking_reasons") or []
    if blocking:
        print("critic blocks:", blocking)

    print("\n--- RISK CHECK ---")
    risk = post("/api/risk/check", {"proposal_id": proposal_id})
    print("approved:", risk.get("approved"))
    print("blocking:", risk.get("blocking_reasons"))
    print("warnings:", risk.get("warnings"))
    if not risk.get("approved"):
        print("ABORT: risk gate rejected")
        raise SystemExit(1)

    print("\n--- LIVE PAPER EXECUTE ---")
    execute = post(f"/api/trades/execute/{proposal_id}", params={"dry_run": "false"})
    print("dry_run:", execute.get("dry_run"))
    print("risk_approved:", execute.get("risk_approved"))
    print("order_id:", execute.get("order_id"))
    print("blocking:", execute.get("blocking_reasons"))
    response = execute.get("alpaca_response") or {}
    print("alpaca_status:", response.get("status"))
    print("alpaca_id:", response.get("id"))
    print("client_order_id:", response.get("client_order_id"))
    print("limit_price:", response.get("limit_price"))
    payload = execute.get("order_payload") or {}
    if payload:
        print("payload_limit:", payload.get("limit_price"))
        print("payload_class:", payload.get("order_class"))

    if not execute.get("order_id") and not response.get("id"):
        print("EXECUTE FAILED OR NO ORDER RETURNED")
        raise SystemExit(1)

    print("\n--- POSITIONS ---")
    positions = get("/api/positions")
    print("open positions:", len(positions))
    for position in positions[:10]:
        print(
            f"  {position.get('symbol')} qty={position.get('qty')} "
            f"mv={position.get('market_value')} upl={position.get('unrealized_pl')}"
        )

    print("\n--- ORDERS ---")
    orders = get("/api/orders")
    for order in orders[:5]:
        print(f"  {order.get('symbol')} status={order.get('status')} id={order.get('id')}")

    print("\n--- MONITOR ---")
    monitor = post("/api/monitor/run", {"sync_orders": "true", "dry_run": "true"})
    print("summary:", monitor.get("summary"))
    for decision in monitor.get("decisions", [])[:5]:
        print(
            f"  {decision.get('symbol')} action={decision.get('action')} "
            f"close={decision.get('should_close')}"
        )

    print("\n" + "=" * 60)
    print("RUN COMPLETE")
    print("scan_run:", scan["run_id"])
    print("proposal_id:", proposal_id)
    print("execute_run:", execute.get("run_id"))
    print("order_id:", execute.get("order_id") or response.get("id"))
    print("=" * 60)


if __name__ == "__main__":
    main()
