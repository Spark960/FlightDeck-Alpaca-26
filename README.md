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

The application scaffold is created in the next build phase. Once backend and frontend projects exist:

```bash
cp .env.example .env
```

Then add Alpaca paper credentials to `.env`. The app must still run in demo mode without credentials.

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
