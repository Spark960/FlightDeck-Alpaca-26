import json
import sys

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"


def show(label: str, response: httpx.Response) -> None:
    print(f"=== {label} {response.status_code} ===")
    try:
        print(json.dumps(response.json(), indent=2)[:1500])
    except Exception:
        print(response.text[:500])
    print()


def main() -> None:
    client = httpx.Client(timeout=60)
    show("settings", client.get(f"{BASE}/api/settings"))
    show("scan", client.post(f"{BASE}/api/scan", json={"limit": 3}))
    proposal = client.post(f"{BASE}/api/proposals", json={"symbol": "SPY", "direction": "bullish"}).json()
    show("proposal", httpx.Response(200, json=proposal))

    if proposal.get("proposal_id"):
        proposal_id = proposal["proposal_id"]
        show("review", client.post(f"{BASE}/api/proposals/review", json={"proposal_id": proposal_id}))
        show("risk", client.post(f"{BASE}/api/risk/check", json={"proposal_id": proposal_id}))
        show(
            "execute dry-run",
            client.post(f"{BASE}/api/trades/execute/{proposal_id}", params={"dry_run": "true"}),
        )
    else:
        print("Proposal rejected under live filters; testing pipeline with inline payload.")
        demo = {
            "accepted": True,
            "underlying_symbol": "SPY",
            "strategy_type": "bull_call_debit_spread",
            "direction": "bullish",
            "expiration": "2026-09-18",
            "estimated_net_debit": 255,
            "max_loss": 255,
            "legs": [
                {
                    "side": "buy",
                    "symbol": "SPY260918C00640000",
                    "type": "call",
                    "strike": 640,
                    "bid": 5.0,
                    "ask": 5.2,
                    "quote_timestamp": "2026-08-30T12:00:00+00:00",
                },
                {
                    "side": "sell",
                    "symbol": "SPY260918C00645000",
                    "type": "call",
                    "strike": 645,
                    "bid": 2.45,
                    "ask": 2.6,
                    "quote_timestamp": "2026-08-30T12:00:00+00:00",
                },
            ],
        }
        show("review demo", client.post(f"{BASE}/api/proposals/review", json={"proposal": demo}))
        show("risk demo", client.post(f"{BASE}/api/risk/check", json={"proposal": demo}))

    show("cli status", client.get(f"{BASE}/api/integrations/cli/status"))
    show("cli proof", client.post(f"{BASE}/api/integrations/cli/run"))
    show("monitor", client.post(f"{BASE}/api/monitor/run", params={"sync_orders": "false", "cli_proof": "true"}))


if __name__ == "__main__":
    main()
