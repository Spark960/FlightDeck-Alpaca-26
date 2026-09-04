# FlightDeck Alpha — Mega System Reference

A single-document snapshot of the entire project as of the hackathon build. Use this as the canonical index. Anything not here is in code, and code is the source of truth.

---

## 1. Project identity

- **Name**: FlightDeck Alpha
- **Hackathon**: [Alpaca AI Trading Agents Hackathon](https://lablab.ai/ai-hackathons/alpaca-ai-trading-agents-hackathon)
- **Dates**: August 28 - September 4, 2026
- **Track**: Options Alpha Agents
- **Prize pool**: $6,300
- **Working directory**: `L:\vs code projects\hackathons\alpaca26`

One-liner:

> FlightDeck Alpha is an autonomous options-trading agent that scans liquid symbols, selects defined-risk options strategies, executes approved trades through Alpaca paper trading, and records a replayable audit trail for every decision.

## 2. Hackathon requirements (verbatim)

| Requirement | How it is satisfied | Reference |
|---|---|---|
| Autonomous AI trading agent | `app/agents/analyst.py` — `analyze_and_critique()` produces a strict-JSON thesis, a critic validates it, deterministic code owns execution. | `backend/app/agents/analyst.py` |
| Uses Alpaca Trading API | `app/alpaca_client.py: AlpacaGateway` wraps `TradingClient`, `StockHistoricalDataClient`, `OptionHistoricalDataClient` from `alpaca-py`. | `backend/app/alpaca_client.py` |
| Uses Alpaca MCP or CLI | CLI proof path: `app/integrations/alpaca_cli.py: run_alpaca_cli()` shells out to the `alpaca` binary, persists JSON output as `agent_events`. | `backend/app/integrations/alpaca_cli.py` |
| Options trading | `app/trading/option_selector.py: select_debit_spread()` selects bull call / bear put debit spreads with single-leg fallback. | `backend/app/trading/option_selector.py` |
| Paper trading | `ALPACA_PAPER=true` is the only allowed mode; risk gate hard-blocks live (`risk.py:32`). | `backend/app/trading/risk.py` |
| Fresh $100k paper account | Required at submission time. Not yet done. | `docs/phase-checklists.md` Phase 11 |
| One-page write-up | Required. Not yet written. | `docs/submission-tracker.md` |

## 3. Tech stack

| Layer | Choice | Version |
|---|---|---|
| Backend language | Python | 3.12 |
| Backend framework | FastAPI | 0.116.1 |
| Backend server | Uvicorn | 0.35.0 |
| Alpaca SDK | `alpaca-py` | 0.42.0 |
| HTTP client | `httpx` | 0.28.1 |
| Validation | `pydantic` | 2.11.7 |
| DB | SQLite (stdlib `sqlite3`) | bundled |
| Frontend language | TypeScript | latest from `frontend/node_modules/typescript` |
| Frontend framework | React + Vite | bundled |
| LLM | Gemini (`gemini-2.5-flash` default, OpenAI-compatible endpoint) | external |
| Scheduler | External (GitHub Actions or Render Cron) | n/a |
| Deployment | Render (API) + Vercel (frontend) | managed |

## 4. Repository layout

```text
alpaca26/
├── README.md
├── HACKATHON_WIN_PLAN.md
├── .env.example
├── .gitignore
├── backend/
│   ├── README.md
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, /health, /api/settings, router includes
│   │   ├── config.py                # pydantic Settings dataclass, env loader
│   │   ├── db.py                    # SQLite connection, SCHEMA
│   │   ├── alpaca_client.py         # AlpacaGateway: account, positions, orders, options, data
│   │   ├── demo_data.py             # Demo-mode fixtures
│   │   ├── dependencies.py          # get_alpaca_gateway() DI
│   │   ├── routes/
│   │   │   ├── account.py
│   │   │   ├── audit.py
│   │   │   ├── integrations.py      # /api/integrations/cli/{status,run,command,latest}
│   │   │   ├── market.py
│   │   │   ├── monitor.py
│   │   │   ├── options.py
│   │   │   ├── proposals.py
│   │   │   ├── risk.py
│   │   │   ├── scan.py
│   │   │   └── trades.py
│   │   ├── trading/
│   │   │   ├── universe.py          # LIQUID_UNIVERSE = 11 symbols
│   │   │   ├── signals.py           # rank_candidates()
│   │   │   ├── option_selector.py   # select_debit_spread()
│   │   │   ├── order_builder.py     # build_order_payload()
│   │   │   ├── order_sync.py        # sync_open_orders()
│   │   │   ├── risk.py              # evaluate_risk()
│   │   │   └── monitor.py           # run_monitor(), evaluate_position()
│   │   ├── agents/
│   │   │   └── analyst.py           # analyze_and_critique()
│   │   ├── integrations/
│   │   │   └── alpaca_cli.py        # run_alpaca_cli(), run_cli_proof()
│   │   └── storage/
│   │       └── audit.py             # create_run, record_*, get_*, list_*
│   ├── scripts/
│   │   └── alpaca_cli_proof.py
│   └── tests/
│       ├── conftest.py
│       ├── test_alpaca_*.py
│       ├── test_analyst.py
│       ├── test_executor.py
│       ├── test_monitor.py
│       ├── test_monitor_integration.py
│       ├── test_order_*.py
│       └── test_risk.py
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── public/
│   └── src/
│       ├── main.tsx
│       ├── App.tsx                  # routes: /, /replay, /positions, /risk, /settings
│       ├── api/client.ts
│       ├── components/              # Card, Layout, StateViews, StatusBadge
│       └── pages/                   # CockpitPage, PositionsPage, ReplayPage, RiskPage, SettingsPage
├── docs/
│   ├── README.md
│   ├── architecture.md
│   ├── architecture-diagram.md      # Mermaid
│   ├── backtesting.md
│   ├── deployment-and-autonomy.md
│   ├── implementation-roadmap.md
│   ├── phase-checklists.md
│   ├── acceptance-checks.md
│   ├── trading-runbook.md
│   ├── social-plan.md
│   ├── submission-tracker.md
│   └── MEGA_SYSTEM_REFERENCE.md     # this file
└── HACKATHON_WIN_PLAN.md
```

## 5. Data model (SQLite)

All tables live in `backend/flightdeck_alpha.db`. Schema is in `backend/app/db.py`.

| Table | Purpose | Key columns |
|---|---|---|
| `system_runs` | One row per agent cycle (scan, proposal, risk, execution, monitor, cli_proof) | `run_id`, `run_type`, `status`, `started_at`, `completed_at`, `summary_json` |
| `market_snapshots` | Universe-level stock snapshots + historical bars | `run_id`, `symbols_json`, `payload_json`, `created_at` |
| `option_chains` | Option chain and contracts for a single underlying per run | `run_id`, `underlying_symbol`, `payload_json`, `created_at` |
| `trade_proposals` | Structured proposals with `accepted` flag, legs, max loss | `proposal_id`, `run_id`, `payload_json`, `created_at` |
| `risk_checks` | Every risk-gate decision, approved or not | `run_id`, `proposal_id`, `approved`, `payload_json`, `created_at` |
| `orders` | One row per submitted order (request + response + ids) | `order_id`, `run_id`, `proposal_id`, `client_order_id`, `request_json`, `response_json`, `created_at` |
| `position_snapshots` | Account + positions taken at monitor time | `run_id`, `payload_json`, `created_at` |
| `agent_events` | Free-form typed events (analyst_proposal, critic_result, monitor_decision, monitor_alert, monitor_action, alpaca_cli_command, market_scan_ranked) | `run_id`, `event_type`, `payload_json`, `created_at` |

`client_order_id` is generated as `FDA-{run_id}-{symbol}-{timestamp}` and capped at 48 chars (`backend/app/storage/audit.py:13`). This is what makes the API idempotent against duplicate cron ticks.

## 6. API surface

All endpoints are prefixed `/api` except `/health`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness, paper/demo flags |
| GET | `/api/settings` | Public settings (no secrets) |
| GET | `/api/account` | Alpaca account snapshot |
| GET | `/api/clock` | Market clock |
| GET | `/api/positions` | Open positions |
| GET | `/api/orders` | Recent orders |
| GET | `/api/market/snapshot?symbols=...` | Stock snapshots |
| GET | `/api/options/contracts/{symbol}` | Option contracts list |
| GET | `/api/options/chain/{symbol}` | Option chain + snapshots |
| POST | `/api/scan` | Rank candidates (uses `LIQUID_UNIVERSE`) |
| POST | `/api/proposals` | Build a structured debit-spread proposal |
| GET | `/api/proposals/{proposal_id}` | Fetch a stored proposal |
| POST | `/api/proposals/review` | Run analyst + critic against a proposal |
| POST | `/api/trades/execute/{proposal_id}?dry_run=...` | Risk-gate + submit (or dry-run) |
| POST | `/api/trades/sync` | Sync open orders from Alpaca |
| GET | `/api/trades/orders/{order_id}/status?refresh=...` | Stored order + optional refresh |
| POST | `/api/monitor/run` | Monitor loop, optional CLI proof + close execution |
| GET | `/api/monitor/latest` | Recent monitor events |
| GET | `/api/audit/runs?limit=...` | List runs for the Replay page |
| GET | `/api/audit/runs/{run_id}` | Full detail of one run |
| GET | `/api/integrations/cli/status` | Is the `alpaca` binary on PATH? |
| GET | `/api/integrations/cli/latest` | Recent CLI invocations |
| POST | `/api/integrations/cli/run` | Run the default proof commands |
| POST | `/api/integrations/cli/command` | Run an arbitrary CLI command |

## 7. Risk gate (the single most important piece of code)

`backend/app/trading/risk.py: evaluate_risk()` is the only place where a trade can become executable. Blocking reasons are hard-coded; the function is pure given inputs. The blocking rules are:

- `paper_trading_required` — `ALPACA_PAPER` must be `true`.
- `account_equity_unavailable` — must have positive equity.
- `buying_power_unavailable` — must have positive buying power.
- `market_not_open` — Alpaca clock says closed.
- `inside_end_of_day_entry_cutoff` — within 10 minutes of close.
- `unsupported_strategy` — strategy must be in `{bull_call_debit_spread, bear_put_debit_spread, long_call, long_put}`.
- `unsupported_or_naked_option_structure` — leg structure must match the strategy.
- `max_loss_unavailable` — `max_loss` must be present and > 0.
- `max_risk_per_trade_exceeded` — `max_loss` > `equity * max_risk_per_trade_pct / 100` (default 1.5%).
- `insufficient_buying_power` — `premium` > `buying_power`.
- `max_open_option_trades_exceeded` — open option positions >= `MAX_OPEN_OPTION_TRADES` (default 5).
- `max_same_underlying_exposure_exceeded` — same-underlying positions >= `MAX_SAME_UNDERLYING_TRADES` (default 2).
- `max_total_premium_deployed_exceeded` — `premium` > `equity * max_total_premium_pct / 100` (default 20%).
- `missing_option_quote` — any leg has no bid/ask.
- `option_spread_too_wide` — leg bid/ask spread > 20%.
- `stale_option_quote` — leg quote timestamp > 15 minutes old.
- `expiration_too_close` — expiration within 7 days.
- `max_drawdown_exceeded` — equity drawdown > `MAX_DRAWDOWN_PCT` (default 8%).
- `max_daily_loss_exceeded` — daily equity change < `-MAX_DAILY_LOSS_PCT` (default 3%).

All limits are env-tunable via the corresponding `MAX_*` variables in `.env.example`.

## 8. Trading pipeline (end-to-end)

```text
15-min cycle
   |
   v
1.  POST /api/scan
      universe = LIQUID_UNIVERSE
      snapshots -> features -> scores -> ranked candidates
      record_market_snapshot, record_agent_event("market_scan_ranked")
   |
   v
2.  POST /api/proposals
      contracts = gateway.option_contracts(top.symbol)
      chain    = gateway.option_chain(top.symbol)
      proposal = select_debit_spread(...)        # or single-leg fallback
      record_option_chain, record_trade_proposal
   |
   v
3.  POST /api/proposals/review
      analyst -> AnalystProposal(thesis, evidence, invalidation, holding, confidence)
      critic  -> CriticResult(passed, blocking_reasons, warnings)
      record_agent_event("analyst_proposal"), record_agent_event("critic_result")
   |
   v
4.  POST /api/trades/execute/{proposal_id}?dry_run=...
      account = gateway.account()
      clock   = gateway.clock()
      risk    = evaluate_risk(proposal, account, clock, positions, settings)
      record_risk_check(approved, payload)
      if approved:
        payload = build_order_payload(proposal, client_order_id)
        if not dry_run:
          response = gateway.submit_order(payload)
          record_order(run_id, client_order_id, payload, response)
   |
   v
5.  POST /api/monitor/run?sync_orders=true&cli_proof=true
      account  = gateway.account()
      positions= gateway.positions()
      orders   = gateway.orders()
      record_position_snapshot
      synced   = sync_open_orders(gateway)
      decisions= run_monitor(account, positions, orders, proposals, settings)
      record_agent_event("monitor_decision", d) for d in decisions
      record_agent_event("monitor_alert", a)   for a in alerts
      if execute_closes=true: submit close orders for should_close decisions
      if cli_proof=true: run_cli_proof()
```

## 9. CLI integration proof

`backend/app/integrations/alpaca_cli.py` runs the `alpaca` binary in a subprocess with `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_LIVE_TRADE=false` set. Default proof commands:

| Label | Command |
|---|---|
| `account` | `alpaca account get` |
| `positions` | `alpaca position list` |
| `open_orders` | `alpaca order list --status open` |
| `clock` | `alpaca clock` |
| `options_chain` | `alpaca data option chain --underlying-symbol SPY --limit 5` |

Each invocation is parsed for JSON. Failures are captured with exit code, stdout, stderr. Every invocation is persisted as an `agent_events` row of type `alpaca_cli_command`. The `demo_mode=True` path returns canned responses shaped like Alpaca output so the integration is testable without a CLI binary on the host.

## 10. Frontend routes

| Path | Page | What it shows |
|---|---|---|
| `/` | `CockpitPage` | Equity, buying power, market open/closed, latest proposal, risk-gate status, positions table, orders, monitor decisions, recent audit runs |
| `/positions` | `PositionsPage` | Open positions with cost basis, market value, unrealized P&L; "Run monitor" button |
| `/replay` | `ReplayPage` | Left: list of audit runs. Right: full run detail (summary, snapshots, proposals, risk checks, orders, position snapshots, agent events) |
| `/risk` | `RiskPage` | Risk-console view (latest risk checks, block reasons) |
| `/settings` | `SettingsPage` | Public settings + key toggles display |

Loading, error, and empty states are handled in `frontend/src/components/StateViews.tsx`.

## 11. Environment variables (from `.env.example`)

| Var | Default | Purpose |
|---|---|---|
| `APP_NAME` | `FlightDeck Alpha` | Display name |
| `ENVIRONMENT` | `development` | Label only |
| `DEMO_MODE` | `true` | If `true`, all Alpaca calls return fixtures |
| `ALPACA_API_KEY` | — | Paper key |
| `ALPACA_SECRET_KEY` | — | Paper secret |
| `ALPACA_PAPER` | `true` | Hard requirement of the hackathon |
| `ALPACA_TRADING_BASE_URL` | `https://paper-api.alpaca.markets/v2` | Trading REST |
| `ALPACA_DATA_BASE_URL` | `https://data.alpaca.markets` | Market data |
| `DATABASE_URL` | `sqlite:///./flightdeck_alpha.db` | Audit store |
| `MAX_RISK_PER_TRADE_PCT` | `1.5` | Per-trade cap |
| `MAX_DAILY_LOSS_PCT` | `3.0` | Daily halt |
| `MAX_TOTAL_DRAWDOWN_PCT` | `8.0` | Total halt |
| `MAX_OPEN_OPTION_TRADES` | `5` | Portfolio cap |
| `MAX_SAME_UNDERLYING_TRADES` | `2` | Concentration cap |
| `MAX_TOTAL_PREMIUM_DEPLOYED_PCT` | `20.0` | Capital cap |
| `MAX_OPTION_BID_ASK_SPREAD_PCT` | `15.0` | Liquidity floor (note: not currently read by `risk.py`; selector uses 20%) |
| `OPTION_QUOTE_MAX_AGE_SECONDS` | `120` | Quote freshness (selector uses 900s) |
| `AGENT_BASE_URL` | `https://generativelanguage.googleapis.com/v1beta/openai/` | OpenAI-compatible |
| `AGENT_MODEL` | `gemini-2.5-flash` | Model id |
| `GEMINI_API_KEY` / `OPENAI_API_KEY` | — | LLM credential |
| `ALPACA_CLI_BINARY` | `alpaca` | Path to the `alpaca` CLI binary |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated list |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Frontend -> backend in production |

> The two pairs of `MAX_OPTION_BID_ASK_SPREAD_PCT` / `OPTION_QUOTE_MAX_AGE_SECONDS` are listed in `.env.example` but the actual values used by the selector are hard-coded at `20%` and `900s`. Either update `option_selector.py` to read these env vars, or remove them from `.env.example` to avoid confusion.

## 12. Build phase status (from `docs/phase-checklists.md`)

| Phase | Description | Status |
|---|---|---|
| 0 | Scope lock | DONE |
| 1 | Alpaca connectivity spine | DONE (proof video not yet recorded) |
| 2 | Persistence + audit | DONE |
| 3 | Market scanner | DONE |
| 4 | Options selector | DONE |
| 5 | AI analyst + critic | DONE |
| 6 | Risk gate | DONE |
| 7 | Execution layer | DONE |
| 8 | Position monitor | DONE |
| 9 | Frontend | DONE (proof-of-judge-clarity recording not yet done) |
| 10 | Deployment | NOT STARTED |
| 11 | Final $100k paper account | NOT STARTED |
| 12 | Submission package | NOT STARTED |

## 13. Open / known issues

These are not bugs in the build, they are scope decisions worth flagging in the submission write-up:

- **No MCP server** — only the CLI proof path is implemented. The hackathon allows either, but adding MCP is a quick win for "AI agent" framing.
- **No in-process scheduler** — autonomy is driven by external cron. The 15-minute cadence is policy, not a system constraint.
- **No backtester yet** — the code is structured so a backtest gateway is a 1-file drop-in, but it has not been built. See `docs/backtesting.md`.
- **Demo mode defaults to `true`** — to prove real paper trading, set `DEMO_MODE=false` and verify with `GET /api/settings`.
- **Selector uses hard-coded spread (20%) and quote-age (900s) instead of the env vars** in `.env.example`. Either wire them up or drop the env vars.
- **Position persistence** — the schema has a `position_snapshots` table, populated at monitor time, but there is no P&L time-series endpoint. Acceptable for the hackathon; would be the first thing to add post-submission.
- **Mid-quote entry assumption** — orders are priced at the bid/ask midpoint. Real fills will deviate. For paper trading this is fine; in production it would need a slippage model.

## 14. Submission assets to produce (with current progress)

| Asset | Status |
|---|---|
| Project title (FlightDeck Alpha) | DONE |
| Short description | drafted in `submission-tracker.md` |
| Long description | not yet drafted |
| Tags | drafted in `submission-tracker.md` |
| Cover image | not yet produced |
| Demo video (<=5 min) | not yet recorded |
| Slide deck (<=10 slides) | not yet produced |
| One-page write-up | not yet written |
| Public GitHub repo | not yet pushed |
| Hosted demo URL | not yet deployed |
| Alpaca paper account ID | not yet created |
| 3-5 social post links | not yet posted |

## 15. Time budget remaining

Assumption: today is **September 3, 2026**; deadline is **September 4, 2026 EOD** (~24-48 hours).

Recommended allocation:

- **0-2h**: provision fresh Alpaca paper account, plug keys in, run a full paper cycle on Render staging.
- **2-8h**: deploy to Render + Vercel, smoke test the hosted URL, install `alpaca` CLI on the Render host.
- **8-14h**: write one-pager, draft slide deck, record demo video, export cover image.
- **14-20h**: public GitHub push, submit to lablab, post 2-3 social updates.
- **20-24h**: bug triage, capture evidence screenshots, final README polish.

If time is tighter, the only hard cut is to drop the social posts and accept fewer engagement points. Everything else is on the critical path.

## 16. Doc index (what to read in what order)

1. `README.md` — the product in one minute.
2. `HACKATHON_WIN_PLAN.md` — the strategic and tactical plan; the source for most other docs.
3. `docs/architecture-diagram.md` — visual reference.
4. `docs/architecture.md` — narrative reference.
5. `docs/trading-runbook.md` — operational policy: non-negotiables, pre-market, EOD.
6. `docs/acceptance-checks.md` — the test plan for every phase.
7. `docs/phase-checklists.md` — the build status.
8. `docs/implementation-roadmap.md` — the long-form build plan.
9. `docs/deployment-and-autonomy.md` — ship to public, run autonomously.
10. `docs/backtesting.md` — extend to historical eval.
11. `docs/submission-tracker.md` — final upload checklist.
12. `docs/social-plan.md` — engagement plan.
13. This file — `docs/MEGA_SYSTEM_REFERENCE.md` — single source of truth index.

## 17. Direct answers to common questions

- **What does the LLM do, exactly?** It writes a thesis in a strict JSON schema (`AnalystProposal`): `thesis`, `evidence`, `invalidation_condition`, `expected_holding_period`, `confidence_score`. A second LLM call (`critic`) checks it against the proposal and either passes or rejects. The LLM never decides to place a trade. Code in `agents/analyst.py`.
- **What does deterministic code do, exactly?** It picks the universe, scores features, picks a debit spread, validates the spread, sizes the trade, checks the risk limits, builds the order payload, and submits. Code in `trading/*`.
- **How is the audit replay built?** Every state-mutating call inserts a row into one of the audit tables. The Replay page reads `system_runs` and joins to the others for a given `run_id`. See `routes/audit.py` and `pages/ReplayPage.tsx`.
- **Why CLI not MCP?** It was the simpler of the two. Adding MCP later is a thin wrapper.
- **Why is `paper_trading_required` the first blocking reason?** Hard-coded defense against accidentally flipping `ALPACA_PAPER=false`. The risk gate refuses to ever run in live mode, regardless of any other config.
- **Why no in-process scheduler?** External schedulers are easier to reason about, easier to redeploy, and the code is fully idempotent via `client_order_id`. A scheduler would also prevent zero-downtime deploys of the API tier.

---

_Last updated_: same day as the latest code review. If code and this doc disagree, the code wins — but please update this file.
