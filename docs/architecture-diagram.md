# FlightDeck Alpha — Architecture Diagram

Source-of-truth architecture for the FlightDeck Alpha autonomous options-trading agent. Rendered natively in GitHub, VS Code, and most Mermaid-compatible viewers.

The diagram is split into logical layers: the **operator surface** (top), the **FastAPI control plane** (middle), the **Alpaca infrastructure** (right), the **persistence / audit store** (left), and the **autonomous pipeline** (bottom).

```mermaid
flowchart TB
    %% Operator / Judge surface
    subgraph SURFACE["Operator & Judge Surface"]
        direction LR
        USER(["Judge or Operator<br/>(browser)"])
        DASH["React + Vite Cockpit<br/>CockpitPage / PositionsPage /<br/>ReplayPage / RiskPage / SettingsPage"]
        CLI["Operator CLI<br/>(curl or scripts)"]
    end

    %% FastAPI control plane
    subgraph API["FastAPI Control Plane (backend/app)"]
        direction TB
        MAIN["app.main: FastAPI app<br/>CORS + /health + /api/settings"]
        ROUTES["app.routes.*<br/>account · audit · integrations<br/>market · monitor · options<br/>proposals · risk · scan · trades"]
        DEPS["app.dependencies<br/>get_alpaca_gateway()"]
    end

    %% Domain modules
    subgraph DOMAIN["Domain Engines (backend/app/trading + agents)"]
        direction TB
        UNIVERSE["trading.universe<br/>LIQUID_UNIVERSE = 11 symbols"]
        SIGNALS["trading.signals<br/>rank_candidates()"]
        SELECTOR["trading.option_selector<br/>select_debit_spread()"]
        BUILDER["trading.order_builder<br/>build_order_payload()"]
        RISK["trading.risk<br/>evaluate_risk()"]
        MONITOR["trading.monitor<br/>run_monitor()"]
        SYNC["trading.order_sync<br/>sync_open_orders()"]
        ANALYST["agents.analyst<br/>analyze_and_critique()"]
    end

    %% Alpaca infrastructure
    subgraph ALPACA["Alpaca Infrastructure"]
        direction TB
        GATEWAY["app.alpaca_client<br/>AlpacaGateway<br/>(demo + paper + live)"]
        CLIINT["app.integrations.alpaca_cli<br/>run_alpaca_cli()<br/>(subprocess -> binary)"]
        TRADE[("Alpaca Trading API<br/>paper-api.alpaca.markets/v2<br/>Account · Orders · Options")]
        DATA[("Alpaca Market Data<br/>data.alpaca.markets<br/>Stock + Option chains")]
        CLIBIN(["alpaca CLI binary<br/>(github.com/alpacahq/cli)"])
    end

    %% Persistence / audit
    subgraph STORE["Persistence (SQLite via app.db)"]
        direction TB
        AUDIT["app.storage.audit<br/>create_run / record_*<br/>has_recent_monitor_action"]
        DB[("flightdeck_alpha.db<br/>system_runs · market_snapshots<br/>option_chains · trade_proposals<br/>risk_checks · orders<br/>position_snapshots · agent_events")]
    end

    %% Autonomous pipeline
    subgraph LOOP["Autonomous Trading Loop"]
        direction TB
        LOOP_15["15-30 min market cycle<br/>(external cron -> /api endpoints)"]
    end

    %% Edges: Surface -> API
    USER -- "opens hosted URL" --> DASH
    DASH -- "fetch /api/*<br/>(Vite proxy -> :8000)" --> ROUTES
    CLI -- "curl POST" --> ROUTES

    %% Edges: API routes -> domain
    MAIN --> ROUTES
    ROUTES --> DEPS
    ROUTES --> UNIVERSE
    ROUTES --> SIGNALS
    ROUTES --> SELECTOR
    ROUTES --> BUILDER
    ROUTES --> RISK
    ROUTES --> MONITOR
    ROUTES --> SYNC
    ROUTES --> ANALYST
    ROUTES --> CLIINT

    %% Edges: domain pipeline
    UNIVERSE -- "candidate symbols" --> SIGNALS
    SIGNALS -- "ranked candidates +<br/>reason_codes + features" --> SELECTOR
    SELECTOR -- "accepted proposal<br/>legs · max_loss · break_even" --> ANALYST
    ANALYST -- "thesis + critic result" --> RISK
    RISK -- "approved only" --> BUILDER
    BUILDER -- "single-leg or<br/>mleg order payload" --> ROUTES
    MONITOR -- "should_close?" --> ROUTES
    SYNC -- "refreshed status" --> ROUTES

    %% Edges: Gateway <-> Alpaca
    ROUTES -- "TradingClient / DataClient" --> GATEWAY
    GATEWAY -- "REST: account, orders,<br/>options contracts/chain,<br/>submit_order" --> TRADE
    GATEWAY -- "REST: stock snapshots,<br/>stock bars, option chain" --> DATA

    %% Edges: CLI integration
    CLIINT -- "subprocess<br/>alpaca account get ...<br/>alpaca data option chain ..." --> CLIBIN
    CLIBIN -- "ALPACA_API_KEY<br/>ALPACA_SECRET_KEY" --> TRADE
    CLIBIN -- "JSON output" --> CLIINT

    %% Edges: audit store
    ROUTES -- "create_run / complete_run" --> AUDIT
    AUDIT --> DB
    DOMAIN -- "record_market_snapshot<br/>record_option_chain<br/>record_trade_proposal<br/>record_risk_check<br/>record_order<br/>record_position_snapshot<br/>record_agent_event" --> AUDIT
    CLIINT -- "record_agent_event<br/>(alpaca_cli_command)" --> AUDIT
    DASH -- "GET /api/audit/runs<br/>GET /api/audit/runs/{id}" --> AUDIT

    %% Edges: autonomous loop
    LOOP_15 -- "POST /api/scan" --> ROUTES
    LOOP_15 -- "POST /api/proposals" --> ROUTES
    LOOP_15 -- "POST /api/trades/execute/{id}<br/>?dry_run=false" --> ROUTES
    LOOP_15 -- "POST /api/monitor/run<br/>?sync_orders=true&cli_proof=true" --> ROUTES

    %% Styling
    classDef surface fill:#1f2a44,stroke:#7aa2f7,color:#ffffff
    classDef api fill:#0f3a2e,stroke:#7ee787,color:#ffffff
    classDef domain fill:#3a1f0f,stroke:#ffa657,color:#ffffff
    classDef alpaca fill:#2a1f3a,stroke:#bb9af7,color:#ffffff
    classDef store fill:#3a2a0f,stroke:#e0af68,color:#ffffff
    classDef loop fill:#0f2a3a,stroke:#7dcfff,color:#ffffff

    class USER,DASH,CLI surface
    class MAIN,ROUTES,DEPS api
    class UNIVERSE,SIGNALS,SELECTOR,BUILDER,RISK,MONITOR,SYNC,ANALYST domain
    class GATEWAY,CLIINT,TRADE,DATA,CLIBIN alpaca
    class AUDIT,DB store
    class LOOP_15 loop
```

## Reading the diagram

- **Surface -> API**: every UI screen and CLI command goes through the same FastAPI routers in `backend/app/routes/`. There is no side channel.
- **Domain -> Gateway -> Alpaca**: deterministic code in `backend/app/trading/*` never touches the network directly. It calls `AlpacaGateway` (`backend/app/alpaca_client.py`), which switches between `demo_data.py` and the live `alpaca-py` SDK based on `DEMO_MODE` and `ALPACA_PAPER`.
- **Audit-first**: every code path that mutates money (proposal, risk check, order, position snapshot, monitor decision, CLI command) calls into `app.storage.audit` to insert a row before returning. That is what powers the Replay page.
- **CLI is a separate edge**: `app.integrations.alpaca_cli` shells out to the `alpaca` binary (`ALPACA_CLI_BINARY`). It is the hackathon's "MCP **or** CLI" proof, and its JSON output is itself persisted as `agent_events` rows of type `alpaca_cli_command`.
- **Autonomous loop**: there is no in-process scheduler. The same endpoints can be driven by an external cron, GitHub Actions schedule, or a Render cron-job service. The minimum cycle is a `scan -> proposal -> review -> execute -> monitor` sequence, all idempotent through `client_order_id`.

## Layer boundaries (for refactors)

| Layer | Owns | Does NOT own |
|---|---|---|
| `routes/*` | HTTP shape, validation, run IDs, audit calls | Risk math, selector logic, order math |
| `trading/*` | Eligibility, sizing, risk math, order payload shape, exit rules | HTTP, persistence, Alpaca SDK construction |
| `agents/*` | LLM proposal/critique and strict-JSON parsing | Execution, risk, persistence |
| `alpaca_client.py` | SDK construction, demo vs live switching, request/response mapping | Domain logic |
| `integrations/alpaca_cli.py` | Subprocess, JSON parsing, demo fallback, audit logging | Strategy |
| `storage/audit.py` | Schema, JSON serialization, run/row helpers | Business rules |
| `frontend/src/pages/*` | Rendering, fetch, loading/error/empty states | Anything that touches Alpaca directly |

## What is intentionally not in the diagram

- **MCP server** — the hackathon accepts MCP **or** CLI. CLI is wired (`integrations/alpaca_cli.py`); MCP is not. The diagram only shows what is implemented.
- **In-process scheduler** — the design uses external triggers (cron, GH Actions, Render Cron) calling the same endpoints. This keeps the process stateless and easy to redeploy.
- **Live trading** — every `ALPACA_PAPER` switch and risk-gate branch is hard-coded to refuse live mode (`trading/risk.py:32`, `max_drawdown_pct` default `8.0`).
