# FlightDeck Alpha

FlightDeck Alpha is an autonomous options trading agent that scans liquid symbols, selects defined-risk options strategies, executes approved trades through Alpaca paper trading, and records a replayable audit trail for every decision.

## Hackathon Scope

This project is built for the Alpaca AI Trading Agents Hackathon. The product goal is a market-hours agent and dashboard that demonstrates:

- Alpaca Trading API integration in paper mode.
- Alpaca MCP or CLI usage for demonstrable agent infrastructure.
- Options trading with defined-risk debit spreads.
- Deterministic risk gates before any order reaches execution.
- SQLite-backed audit logging for scans, proposals, risk checks, orders, positions, and monitor events.
- Demo mode that works when markets are closed or credentials are absent.

## Strategy

Primary strategy:

- Bull call debit spreads for bullish momentum setups.
- Bear put debit spreads for bearish momentum setups.

Fallback strategy:

- Single-leg long calls or puts if multi-leg option order support blocks the demo path.

The LLM analyst may explain and critique structured trade proposals, but deterministic code owns eligibility, sizing, risk approval, and order submission.

## Stack

- Backend: FastAPI, Python, `alpaca-py`
- Frontend: React, Vite, TypeScript
- Storage: SQLite
- Jobs: simple scheduler or async loop for scans and monitoring
- Broker/data: Alpaca paper Trading API and options market data

## Planned Repository Layout

```text
alpaca26/
  backend/
    app/
      main.py
      config.py
      db.py
      alpaca_client.py
      routes/
      trading/
      agents/
      storage/
    tests/
  frontend/
    src/
      api/
      components/
      pages/
  docs/
```

## Local Setup

```bash
cp .env.example .env
```

Then add Alpaca paper credentials to `.env`.

Useful toggles:

- `DEMO_MODE=false` calls Alpaca with the configured paper credentials.
- `DEMO_MODE=true` uses built-in demo responses for market-closed demos.
- `AGENT_MODEL=gemini-3.7-flash` works with Google's OpenAI-compatible Gemini endpoint.

Run the backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Run the frontend:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` and `/health` to `http://127.0.0.1:8000`.

## API Spine

- `GET /health`
- `GET /api/settings`
- `GET /api/account`
- `GET /api/clock`
- `GET /api/positions`
- `GET /api/orders`
- `GET /api/market/snapshot?symbols=SPY,QQQ,AAPL`
- `GET /api/options/contracts/{symbol}`
- `GET /api/options/chain/{symbol}`
- `POST /api/scan`
- `POST /api/proposals`
- `GET /api/audit/runs`
- `GET /api/audit/runs/{run_id}`
- `GET /api/integrations/cli/status`
- `POST /api/integrations/cli/run`
- `GET /api/integrations/cli/latest`
- `POST /api/monitor/run`

## Alpaca CLI Integration

FlightDeck Alpha uses `alpaca-py` for order execution and the [Alpaca CLI](https://github.com/alpacahq/cli) as the hackathon MCP/CLI proof path. CLI JSON output is persisted to `agent_events` for audit replay.

```bash
# Install Alpaca CLI (see https://github.com/alpacahq/cli)
# Set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env

# Run proof commands (account, positions, orders, clock, options chain)
python scripts/alpaca_cli_proof.py

# Or via API
curl -X POST http://127.0.0.1:8000/api/integrations/cli/run
```

Monitor cycles can optionally include CLI proof with `POST /api/monitor/run?cli_proof=true`.

## Safety Defaults

- Paper mode is required by default.
- Live trading is out of scope.
- No naked short options.
- Every proposed trade must pass the deterministic risk gate.
- Every decision and rejection should be persisted for replay.

## Documentation

- [Implementation roadmap](docs/implementation-roadmap.md)
- [Phase checklists](docs/phase-checklists.md)
- [Acceptance checks](docs/acceptance-checks.md)
- [Trading runbook](docs/trading-runbook.md)
- [Submission tracker](docs/submission-tracker.md)
- [Social plan](docs/social-plan.md)
- [Architecture placeholder](docs/architecture.md)
