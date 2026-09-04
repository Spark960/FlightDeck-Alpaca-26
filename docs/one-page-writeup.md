# FlightDeck Alpha — One-Page Technical Write-Up

## The Problem

Letting an AI agent trade options without strict guardrails is a guaranteed way to blow up your account. LLMs are excellent at analyzing market conditions and articulating a compelling trade thesis, but they are notoriously bad at hard risk management — they hallucinate fills, ignore capital constraints, and cannot natively enforce structural rules like "never sell a naked option." I wanted a system that was fully autonomous, but where I could be 100% certain it couldn't go rogue. The thesis: **let AI handle the reasoning, let deterministic code handle the risk.**

---

## AI Logic

The system wakes up on a fixed cadence (every 15 minutes during US equity market hours, enforced by checking Alpaca's live market clock). A full autonomous cycle has four stages:

**1. Market Scanner (`trading/signals.py`)**
The scanner pulls real-time stock snapshots and options chains for 11 highly liquid symbols (SPY, QQQ, AAPL, TSLA, NVDA, MSFT, AMZN, META, GOOGL, AMD, COIN) via the Alpaca Data API. For each symbol it computes a set of features: 1-day and 5-day price return percentages, volume ratio vs. the 20-day average, and whether a fresh options quote exists. A `rank_candidates()` function scores and sorts the universe, tagging each candidate with directional `reason_codes` (e.g., `bullish_momentum`, `high_relative_volume`, `weak_directional_edge`).

**2. Options Selector (`trading/option_selector.py`)**
The top candidate's live options chain is fetched and filtered. The selector looks for defined-risk debit spread legs: for a bullish signal, it finds the nearest at-the-money long call and a short call 2–5 strikes above it. For bearish, it mirrors this with puts. Legs must have a bid-ask spread under 20% of midpoint and a quote timestamp under 15 minutes old. Max loss, break-even, and estimated net debit are computed from live quotes before the proposal is assembled.

**3. Gemini Analyst + Critic (`agents/analyst.py`)**
The assembled proposal — symbol, direction, strategy type, legs, strikes, and computed risk math — is sent to Gemini via the OpenAI-compatible endpoint with `temperature=0.2`. Gemini is instructed to respond in strict JSON only, with fields: `thesis`, `evidence` (2–6 bullet points), `invalidation_condition`, `expected_holding_period`, and `confidence_score` (0–1). A Pydantic model (`AnalystProposal`) validates the response and rejects it if fields are missing or malformed.

The same module then runs a deterministic **Critic** pass over the analyst's output: it checks that the confidence score is above 0.35, that at least 2 evidence bullets were provided, that the AI's stated direction matches the scanner's signal, and that the proposed strategy type matches the directional thesis (e.g., a bullish thesis must use a bull call spread or long call, never a put structure). If the critic blocks, the proposal dies before it ever reaches the risk engine.

---

## Deterministic Risk Gates (`trading/risk.py`)

Every proposal that survives the Critic is evaluated by a standalone `evaluate_risk()` function. This function has zero LLM involvement — it is pure Python with hardcoded rules. The blocking conditions, in order of evaluation, are:

| Gate | What It Checks |
|---|---|
| `paper_trading_required` | `ALPACA_PAPER=true` must be set; live mode is refused |
| `account_equity_unavailable` | Equity must be > 0; dead accounts are blocked |
| `buying_power_unavailable` | Buying power must be > 0 |
| `market_not_open` | Alpaca's live `is_open` clock flag must be true |
| `inside_end_of_day_entry_cutoff` | No new entries within 10 minutes of market close |
| `unsupported_strategy` | Only `bull_call_debit_spread`, `bear_put_debit_spread`, `long_call`, `long_put` are allowed |
| `unsupported_or_naked_option_structure` | Spread legs are structurally validated; any configuration that implies a naked short is rejected |
| `max_loss_unavailable` | Proposal must carry a computable max loss |
| `max_risk_per_trade_exceeded` | Max loss must be < 1.5% of account equity |
| `insufficient_buying_power` | Estimated net debit must fit within available buying power |
| `max_open_option_trades_exceeded` | Portfolio cannot hold more than 5 open option positions |
| `max_same_underlying_exposure_exceeded` | No more than 2 trades on the same underlying simultaneously |
| `max_total_premium_deployed_exceeded` | Total premium at risk across all positions must stay under 20% of equity |
| `option_spread_too_wide` | Bid-ask spread on any leg must be < 20% of midpoint |
| `missing_option_quote` | Any leg without a live bid/ask is an automatic block |
| `stale_option_quote` | Any leg with a quote timestamp older than 15 minutes is blocked |
| `expiration_too_close` | Expiration must be at least 7 days away |
| `max_drawdown_exceeded` | Account equity must not have fallen > 8% from prior close |
| `max_daily_loss_exceeded` | Intraday loss must not exceed 3% of prior close equity |

If any single gate triggers, `approved: false` is returned, the proposal is killed, and the rejection reason is written to the `risk_checks` table for full audit replay. The AI cannot negotiate with, override, or bypass any of these gates.

---

## Alpaca Infrastructure

**Paper Trading API (`alpaca_client.py`)**: All trade execution runs through `alpaca-py`'s `TradingClient` pointed at `paper-api.alpaca.markets/v2`. The `AlpacaGateway` class wraps account info, market clock, positions, orders, and the `submit_order` call. A `DEMO_MODE` flag switches the gateway to pre-baked deterministic responses so the cockpit can be demoed when markets are closed or credentials are absent — the code path is identical.

**Market Data**: Options chains and stock snapshots are fetched via `alpaca-py`'s `StockHistoricalDataClient` and the options endpoint at `data.alpaca.markets`. Real-time quote freshness is validated before any proposal is generated.

**Alpaca CLI Integration (`integrations/alpaca_cli.py`)**: The `alpaca` CLI binary (built from `github.com/alpacahq/cli`, compiled from Go and embedded in the Docker image) is invoked via `subprocess` to verify live account state, positions, and options chains independently of `alpaca-py`. The raw JSON output is captured and persisted as an `agent_events` row of type `alpaca_cli_command`, giving judges a second independent proof path for Alpaca connectivity that doesn't rely on the Python SDK.

---

## The Audit Trail

Every stage of every cycle — market snapshot, options chain, trade proposal, analyst review, critic result, risk gate decision, order submission, CLI proof, and position snapshot — is written to a SQLite database (`agent_events`, `system_runs`, `trade_proposals`, `risk_checks`, `orders`, `position_snapshots`). The React frontend's **Replay** tab reads the `audit/runs` API and lets you step through the agent's complete decision history in chronological order. You never have to guess why the bot took or rejected a trade. You just open the Replay tab and read its mind.

The system runs completely autonomously, without babysitting.
