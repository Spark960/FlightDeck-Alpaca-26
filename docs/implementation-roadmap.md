# Implementation Roadmap

Project: FlightDeck Alpha

Goal: Build an autonomous, paper-trading options agent using Alpaca's Trading API plus Alpaca MCP or CLI, with defined-risk options strategies, deterministic risk gates, and a replayable audit trail.

Current date: Sunday, August 30, 2026  
Submission deadline: Friday, September 4, 2026

## Success Definition

We are submission-ready when all of these are true:

- [ ] The agent can autonomously scan a liquid universe.
- [ ] The agent can fetch option chains and select valid contracts.
- [ ] The agent can create a structured options trade proposal.
- [ ] The deterministic risk gate can approve or reject proposals with reasons.
- [ ] Approved trades can be submitted to Alpaca paper trading.
- [ ] Orders, fills, positions, and P&L are persisted in an audit log.
- [ ] The dashboard shows the live cockpit and decision replay.
- [ ] A fresh $100,000 Alpaca paper account is used for final judging.
- [ ] Alpaca MCP or CLI usage is present and demonstrable.
- [ ] Public repo, hosted demo, video, slides, write-up, and account ID are ready.

## Build Philosophy

This project should feel like real trading infrastructure compressed into a hackathon demo:

1. LLMs reason and explain.
2. Deterministic code controls money, risk, and execution.
3. Every decision is logged.
4. Demo mode works even when markets are closed.
5. The UI starts inside the product, not on a marketing landing page.

## Phase 0: Setup And Scope Lock

Target duration: 2-3 hours

Purpose: remove ambiguity before coding.

Steps:

- [x] Confirm project name: `FlightDeck Alpha`.
- [x] Confirm stack: FastAPI backend, React/Vite frontend, SQLite, `alpaca-py`.
- [x] Confirm primary strategy: bull call and bear put debit spreads.
- [x] Confirm fallback strategy: single-leg long call/put if multi-leg order support blocks us.
- [x] Confirm demo mode requirement: every main screen must work without market being open.
- [x] Create `.env.example`.
- [x] Create initial README.
- [x] Create architecture diagram placeholder.

Exit check:

- [x] A teammate can explain the product in one sentence.
- [x] The codebase can be scaffolded without further product debate.

## Phase 1: Alpaca Connectivity Spine

Target duration: 4-6 hours

Purpose: prove we can talk to Alpaca before building intelligence on top.

Backend endpoints:

- [x] `GET /health`
- [x] `GET /api/account`
- [x] `GET /api/clock`
- [x] `GET /api/positions`
- [x] `GET /api/orders`
- [x] `GET /api/market/snapshot?symbols=SPY,QQQ,AAPL`
- [x] `GET /api/options/contracts/{symbol}`
- [x] `GET /api/options/chain/{symbol}`

Implementation steps:

- [x] Add settings loader for Alpaca keys and paper mode.
- [x] Add Alpaca trading client.
- [x] Add Alpaca stock data client.
- [x] Add Alpaca option data/client wrapper.
- [ ] Add typed response models.
- [x] Add structured error responses for missing credentials and API failures.
- [x] Add demo/mock responses for market closed or missing credentials.

Exit check:

- [x] Backend starts locally.
- [x] Health endpoint passes.
- [x] Account endpoint works with credentials or returns a helpful credential error.
- [x] At least one stock snapshot can be fetched or mocked.
- [x] At least one options chain can be fetched or mocked.

## Phase 2: Data Store And Audit Foundation

Target duration: 3-4 hours

Purpose: every agent decision needs a persistent paper trail.

Tables:

- [x] `market_snapshots`
- [x] `option_chains`
- [x] `trade_proposals`
- [x] `risk_checks`
- [x] `orders`
- [x] `position_snapshots`
- [x] `agent_events`
- [x] `system_runs`

Implementation steps:

- [x] Add SQLite database setup.
- [x] Add migration or schema creation script.
- [x] Add repository functions for inserts and reads.
- [x] Add run ID for each agent cycle.
- [x] Add client order ID format: `FDA-{run_id}-{symbol}-{timestamp}`.
- [x] Add audit endpoint: `GET /api/audit/runs`.
- [x] Add audit detail endpoint: `GET /api/audit/runs/{run_id}`.

Exit check:

- [x] Every market scan writes a run record.
- [x] Every proposal and rejection can be retrieved.
- [x] Audit detail can power replay UI.

## Phase 3: Universe And Signal Engine

Target duration: 5-7 hours

Purpose: create trade candidates using explainable market features.

Universe v1:

- [x] SPY
- [x] QQQ
- [x] IWM
- [x] AAPL
- [x] MSFT
- [x] NVDA
- [x] AMD
- [x] TSLA
- [x] META
- [x] AMZN
- [x] GOOGL

Features:

- [ ] 1-day return
- [ ] 5-day return
- [ ] 20-day moving average slope
- [ ] intraday move from open
- [ ] gap from previous close
- [ ] volume ratio versus 20-day average
- [ ] realized volatility or ATR proxy
- [x] quote freshness

Signals:

- [x] bullish momentum score
- [x] bearish momentum score
- [ ] volatility/event score
- [x] no-trade score

Implementation steps:

- [x] Build `universe.py`.
- [x] Build `signals.py`.
- [x] Add endpoint `POST /api/scan`.
- [x] Persist scan inputs and outputs.
- [x] Sort candidates by score.
- [x] Add reason codes for each candidate.

Exit check:

- [ ] Scanner returns ranked candidates.
- [ ] Each candidate includes numeric scores and plain-English reason codes.
- [ ] The system can choose "no trade" without error.

## Phase 4: Options Strategy Selector

Target duration: 6-8 hours

Purpose: translate a directional signal into a valid options structure.

Primary strategies:

- [x] Bull call debit spread for bullish signals.
- [x] Bear put debit spread for bearish signals.

Fallback strategies:

- [ ] Single-leg long call for bullish signals.
- [ ] Single-leg long put for bearish signals.

Contract filters:

- [x] Expiration 7-30 days out.
- [x] Tradable contracts only.
- [ ] Near-the-money long leg.
- [ ] Further out-of-the-money short leg.
- [x] Max bid/ask spread threshold.
- [ ] Minimum open interest when available.
- [ ] Minimum option quote freshness.
- [ ] Net debit below max risk budget.
- [ ] Skip contracts with missing prices.

Proposal output:

- [x] underlying symbol
- [x] strategy type
- [x] direction
- [x] expiration
- [x] legs
- [x] estimated net debit
- [x] max loss
- [x] max profit when calculable
- [x] break-even when calculable
- [ ] selected Greeks when available
- [x] selection reason

Exit check:

- [x] Given a bullish candidate, selector returns a bull call spread or a clear rejection.
- [x] Given a bearish candidate, selector returns a bear put spread or a clear rejection.
- [ ] No malformed or stale contract can pass selection.

## Phase 5: AI Analyst And Critic

Target duration: 5-7 hours

Purpose: add agentic reasoning without letting the model bypass controls.

Analyst agent responsibilities:

- [ ] Read only structured market facts and selected option candidates.
- [ ] Produce strict JSON.
- [ ] Explain thesis.
- [ ] List evidence.
- [ ] List invalidation condition.
- [ ] Provide expected holding period.
- [ ] Provide confidence score.

Critic agent responsibilities:

- [ ] Check missing fields.
- [ ] Check contradiction between direction and evidence.
- [ ] Check weak thesis.
- [ ] Check if strategy type matches market signal.
- [ ] Require revision or rejection when evidence is thin.

Schema requirements:

- [ ] JSON schema enforced.
- [ ] Invalid JSON is rejected and logged.
- [ ] Agent cannot provide executable order payload directly.
- [ ] Critic result is persisted.

Exit check:

- [ ] A complete analyst proposal can be generated.
- [ ] The critic can reject a deliberately bad proposal.
- [ ] The risk gate can run without caring which LLM generated the text.

## Phase 6: Deterministic Risk Gate

Target duration: 5-7 hours

Purpose: make the project credible and protect the paper account from nonsense.

Hard checks:

- [ ] Paper mode only.
- [ ] Account equity loaded successfully.
- [ ] Buying power loaded successfully.
- [ ] Market is open for new entries.
- [ ] No new entries in final 10 minutes of regular session.
- [ ] Max risk per trade: default 1.5% of equity.
- [ ] Max daily realized/unrealized loss: default 3%.
- [ ] Max total drawdown: default 8%.
- [ ] Max open option trades: 5.
- [ ] Max same-underlying open trades: 2.
- [ ] Max total premium deployed: 20% of equity.
- [ ] Option quote is fresh.
- [ ] Option spread is below threshold.
- [ ] Expiration is not too close.
- [ ] No naked short options.
- [ ] Strategy is in allowlist.

Outputs:

- [ ] `approved: true/false`
- [ ] `blocking_reasons`
- [ ] `warnings`
- [ ] `computed_risk`
- [ ] `position_size`
- [ ] `max_loss`
- [ ] `timestamp`

Tests:

- [ ] Reject live mode.
- [ ] Reject too-large risk.
- [ ] Reject stale quote.
- [ ] Reject wide spread.
- [ ] Reject unsupported strategy.
- [ ] Approve known-good debit spread.

Exit check:

- [ ] No order can be submitted without a passing risk check.
- [ ] Every risk check is auditable.
- [ ] Risk tests pass.

## Phase 7: Execution Layer

Target duration: 5-8 hours

Purpose: send approved trades to Alpaca paper trading.

Implementation steps:

- [ ] Create order builder for debit spreads.
- [ ] Create fallback single-leg order builder.
- [ ] Use limit orders near midpoint.
- [ ] Add idempotent client order IDs.
- [ ] Submit only after approved risk gate.
- [ ] Persist request payload before submission.
- [ ] Persist Alpaca response after submission.
- [ ] Handle partial fills, rejections, and open orders.
- [ ] Add endpoint `POST /api/trades/execute/{proposal_id}`.
- [ ] Add dry-run mode.

Alpaca MCP or CLI proof:

- [ ] Pick MCP or CLI as the required integration proof.
- [ ] If CLI: run account/order/data commands and persist JSON output.
- [ ] If MCP: document MCP config and tool usage.
- [ ] Show MCP/CLI integration in README and demo.

Exit check:

- [ ] A dry-run approved proposal produces the expected order payload.
- [ ] A real paper-mode order can be submitted.
- [ ] The order appears in Alpaca dashboard or API order list.
- [ ] The audit log links proposal, risk check, and order.

## Phase 8: Position Monitor

Target duration: 4-6 hours

Purpose: keep the agent from being a one-shot order button.

Monitor loop:

- [ ] Poll account.
- [ ] Poll positions.
- [ ] Poll open orders.
- [ ] Poll recent fills.
- [ ] Update P&L.
- [ ] Check take-profit.
- [ ] Check stop-loss.
- [ ] Check time stop.
- [ ] Check expiration risk.
- [ ] Log monitor events.

Exit rules:

- [ ] Take profit at 40%-70% of debit gain.
- [ ] Stop loss at 40%-60% of debit loss.
- [ ] Close before expiration-risk window.
- [ ] Alert if a position lacks expected paired leg.
- [ ] Alert if account drawdown halt triggers.

Exit check:

- [ ] Monitor can run repeatedly without duplicate actions.
- [ ] Monitor updates dashboard state.
- [ ] Monitor can explain why a position is held or closed.

## Phase 9: Dashboard

Target duration: 8-10 hours

Purpose: make the project instantly legible to judges.

Screens:

- [ ] Cockpit
- [ ] Decision Replay
- [ ] Positions
- [ ] Risk Console
- [ ] Settings

Cockpit must show:

- [ ] Equity
- [ ] P&L
- [ ] open risk
- [ ] daily drawdown
- [ ] active positions
- [ ] latest scan
- [ ] latest proposal
- [ ] risk-gate status
- [ ] order status
- [ ] rejected proposal gallery

Replay must show:

- [ ] market snapshot
- [ ] signal scores
- [ ] selected option legs
- [ ] analyst thesis
- [ ] critic result
- [ ] risk-gate reasons
- [ ] order payload and response
- [ ] resulting P&L

Demo mode:

- [ ] Works without credentials.
- [ ] Works when market is closed.
- [ ] Includes at least 3 recorded decisions:
  - approved trade
  - rejected trade
  - monitored open position

Exit check:

- [ ] First screen communicates the product in under 10 seconds.
- [ ] Judges can see both autonomy and safety.
- [ ] No important screen is blank without credentials.

## Phase 10: Deployment

Target duration: 4-6 hours

Purpose: get a stable public demo.

Steps:

- [ ] Decide deployment target.
- [ ] Configure backend environment variables.
- [ ] Configure frontend API URL.
- [ ] Deploy backend.
- [ ] Deploy frontend.
- [ ] Smoke test public URLs.
- [ ] Confirm demo mode works publicly.
- [ ] Confirm no secrets are exposed.

Exit check:

- [ ] Hosted application URL is ready for submission.
- [ ] Public repo has setup instructions.
- [ ] Demo does not crash when Alpaca credentials are absent.

## Phase 11: Final Account And Contest Run

Target duration: ongoing from earliest possible moment

Purpose: generate eligible paper-trading activity.

Steps:

- [ ] Create a brand-new Alpaca paper account for judging.
- [ ] Confirm starting balance is $100,000.
- [ ] Generate paper API keys.
- [ ] Put account ID in private tracker.
- [ ] Run account check.
- [ ] Run scanner.
- [ ] Run first dry-run.
- [ ] Run first approved live paper trade.
- [ ] Monitor orders and positions.
- [ ] Export account/order/position evidence for video.

Exit check:

- [ ] Final submission account has real paper activity.
- [ ] Account ID is ready to submit.
- [ ] P&L and trade history are visible.

## Phase 12: Submission Package

Target duration: 6-8 hours

Purpose: package the thing so judges remember it.

Assets:

- [ ] Cover image
- [ ] Demo video
- [ ] Slide deck
- [ ] One-page write-up
- [ ] Public GitHub repo
- [ ] Hosted app URL
- [ ] Alpaca account ID
- [ ] Social links

Exit check:

- [ ] Someone can review the submission in 5 minutes and understand why it should win.
- [ ] All hard requirements are visibly satisfied.
- [ ] The video shows an actual end-to-end agent cycle.
