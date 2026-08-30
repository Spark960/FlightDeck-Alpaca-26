# Alpaca AI Trading Agents Hackathon Winning Plan

Date prepared: 2026-08-30

## 1. What The Hackathon Actually Rewards

From the supplied hackathon page:

- Event: Alpaca AI Trading Agents Hackathon
- Dates: August 28-September 4, 2026
- Format: online, 7 days
- Prize pool: $6,300 total
- Main challenge: Options Alpha Agents
- Core requirements:
  - Build an autonomous AI trading agent using Alpaca's Trading API.
  - Use either Alpaca's MCP server or Alpaca CLI.
  - Incorporate options trading.
  - Develop and test in Alpaca paper trading.
  - Final judging account must be a brand-new Alpaca paper account.
  - Starting balance must be $100,000.
  - Include a one-page write-up covering AI logic, risk gates, and Alpaca infrastructure implementation.
- Submission requirements:
  - Project title, short description, long description, tags
  - Cover image
  - Video presentation
  - Slide presentation
  - Public GitHub repository
  - Hosted demo application URL
  - Alpaca paper trading account ID
  - Up to 5 social post links
- Judging criteria:
  - P&L performance
  - Technology implementation
  - Creativity and originality
  - Presentation and execution
  - Social engagement

This means the project cannot be only a dashboard, only a backtester, or only a market explainer. It needs to trade options in paper mode, show activity on the submitted account, and communicate the reasoning clearly.

## 2. Research: How Real Trading Systems Are Actually Built

Real systematic trading systems are usually not "one AI prompt that buys things." They are pipelines with separation of duties:

1. Universe selection: decide what symbols are eligible.
2. Signal or alpha generation: generate possible trades.
3. Portfolio construction: decide sizing and target exposures.
4. Risk management: modify, reject, reduce, or exit positions.
5. Execution: place orders and monitor fills.

QuantConnect's Algorithm Framework uses almost exactly this structure: universe selection, alpha creation, portfolio construction, execution, and risk management. Source: https://www.quantconnect.com/docs/v1/algorithm-framework/overview

For AI trading specifically, the strongest production-ish pattern is:

1. LLMs produce structured trade proposals and explanations.
2. Deterministic code validates eligibility, sizing, risk, and order constraints.
3. Execution happens through a broker API.
4. Every decision is logged for audit and post-trade analysis.

Alpaca's own multi-agent trading-system article describes a similar architecture: specialized agents, structured proposals, critic validation, deterministic risk guard, Alpaca execution, and position monitoring. Source: https://alpaca.markets/learn/building-a-multi-agent-ai-trading-system-on-alpaca

Regulated market-access guidance points in the same direction. FINRA emphasizes supervision, software testing, system validation, post-deployment review, and compliance coordination for algorithmic trading. Source: https://www.finra.org/rules-guidance/key-topics/algorithmic-trading

SEC market-access guidance emphasizes automated pre-trade risk controls when electronic systems are involved. Source: https://www.sec.gov/rules-regulations/staff-guidance/trading-markets-frequently-asked-questions/divisionsmarketregfaq-0

For this hackathon, we should borrow the serious engineering shape without pretending this is live-money institutional trading.

## 3. Alpaca-Specific Technical Facts

Useful Alpaca capabilities:

- Paper options trading is enabled by default.
- Alpaca supports option contract lookup through `/v2/options/contracts`.
- The same Orders API is used for options as for equities and crypto, with options-specific validations.
- Options market data includes historical and real-time option data.
- Alpaca MCP exposes tools for account, orders, positions, assets, stock data, options data, news, and watchlists.
- Alpaca MCP supports `place_option_order`, `get_option_chain`, `get_option_snapshot`, and option Greeks/IV.
- Alpaca CLI is intended for agents, scripts, automation, cron jobs, and CI, and paper trading is the default.

Sources:

- Alpaca options docs: https://docs.alpaca.markets/us/docs/options-trading
- Alpaca MCP docs: https://docs.alpaca.markets/us/docs/alpaca-mcp-server
- Alpaca CLI GitHub: https://github.com/alpacahq/cli
- Alpaca options tutorial: https://alpaca.markets/learn/how-to-trade-options-with-alpaca
- Alpaca paper trading docs: https://docs.alpaca.markets/us/v1.4.2/docs/paper-trading

Important paper-trading caveat:

Paper trading is good for the hackathon because it is required, but it does not fully model market impact, information leakage, slippage, order queue position, price improvement, fees, dividends, or some liquidity constraints. The product should disclose that honestly and use limit orders plus liquidity filters to look serious.

## 4. Winning Product Concept

Project name: FlightDeck Alpha

One-liner:

FlightDeck Alpha is an autonomous options trading agent that scans liquid symbols, selects defined-risk options strategies, executes them through Alpaca paper trading, and produces a replayable audit trail for every decision.

Why this is better than a generic trading bot:

- It satisfies every hard requirement: autonomous agent, Alpaca Trading API, MCP/CLI, options trading, paper account.
- It competes on P&L with realistic, limited-risk options strategies.
- It has a strong demo: signal to strategy to risk gate to order to portfolio impact.
- It feels closer to real trading infrastructure because the LLM is not trusted with raw execution.
- It gives judges a memorable object: a trading "flight recorder" for AI decisions.

Core demo sentence:

"Most AI trading demos show you an agent placing an order. We show you the entire control tower: market scan, thesis, option-chain selection, Greeks, risk gates, execution, monitoring, and post-trade replay."

## 5. Strategy Choice

We should not build a complex, fragile options monster. We should build 2-3 simple strategy templates and let the agent choose among them.

Primary strategy: debit spread momentum

- Bull call debit spread for bullish setups.
- Bear put debit spread for bearish setups.
- Defined maximum loss equals net debit paid.
- Easier to explain.
- Suitable for Level 3 paper options.
- Lower blow-up risk than naked short premium.

Secondary strategy: long straddle or long strangle around high-momentum/event uncertainty

- Used only when expected move/volatility conditions justify it.
- Defined loss: premium paid.
- Useful for dramatic demos because it uses multi-leg options.
- Risk: premium decay can hurt if the underlying does not move.

Tertiary strategy: cash-secured put or covered call only if we want income flavor

- Useful but less exciting for a 7-day contest.
- Can tie up capital.
- Assignment/expiration complexity is not worth making it the main wedge.

Recommended final:

Build debit spreads first. Add straddle/strangle only after the spread path works end to end.

Options risk rules to copy from serious practice:

- Trade only liquid underlyings.
- Trade only contracts with tight bid/ask spread.
- Prefer near-the-money or slightly out-of-the-money strikes.
- Avoid expiration day unless explicitly building a 0DTE mode.
- Avoid holding short legs into expiration without monitoring.
- Cap premium at risk per trade.
- Track Greeks, especially delta, gamma, theta, and vega.

Options education sources:

- Cboe options liquidity overview: https://optionsfacts.cboe.com/
- Cboe strategy-based margin overview: https://www.cboe.com/us/options/strategy_based_margin
- OIC calendar/diagonal spreads risk notes: https://www.optionseducation.org/news/september-webinar-key-takeaways-what-are-calendar-diagonal-spreads

## 6. System Architecture

Use this architecture:

1. Data Ingestion
   - Pull account, clock, positions, orders.
   - Pull stock snapshots/bars for a watchlist.
   - Pull option chains and option snapshots for candidates.
   - Pull Alpaca news if available.

2. Universe Selector
   - Start with a curated liquid universe:
     - SPY, QQQ, IWM
     - AAPL, MSFT, NVDA, AMD, TSLA, META, AMZN, GOOGL
   - Filter by:
     - options enabled
     - market open
     - sufficient volume
     - not already overexposed

3. Signal Engine
   - Compute:
     - 1-day and 5-day returns
     - intraday momentum
     - ATR or realized volatility
     - gap from previous close
     - volume ratio
     - moving-average slope
   - Output candidate directional bias:
     - bullish
     - bearish
     - volatility/event
     - no trade

4. Options Strategy Selector
   - For bullish: bull call debit spread.
   - For bearish: bear put debit spread.
   - For volatility/event: long straddle or strangle.
   - Contract filters:
     - expiration 7-30 days out
     - bid/ask spread below configured threshold
     - open interest/volume above threshold when available
     - max premium at risk below budget
     - Greeks within policy range

5. AI Analyst Agent
   - Reads structured market facts, not raw web chaos.
   - Produces a strict JSON proposal:
     - symbol
     - market regime
     - strategy type
     - legs
     - thesis
     - evidence
     - invalidation condition
     - expected holding period
     - max loss
     - confidence
   - The LLM must never directly submit orders.

6. Critic Agent
   - Reviews the proposal for missing fields, weak evidence, contradictory reasoning, and strategy-policy violations.
   - Can mark:
     - pass
     - revise
     - reject

7. Deterministic Risk Gate
   - Hard code these checks:
     - paper mode only
     - max risk per trade: 1.0%-2.0% of equity
     - max daily loss: 3.0%
     - max total drawdown: 6.0%-8.0%
     - max open trades: 5
     - max same-underlying exposure: 2 trades
     - max options premium deployed: 15%-25% of equity
     - no order if quote stale
     - no order if spread too wide
     - no order in final 10 minutes unless closing
     - no new short-leg strategy on expiration day
   - Risk gate returns machine-readable reasons for rejections.

8. Execution Layer
   - Uses Alpaca Trading API directly.
   - Uses Alpaca MCP or CLI for hackathon compliance and visible integration.
   - Place option orders as limit orders near midpoint, not blind market orders.
   - Record Alpaca order ID, client order ID, status, and fill.

9. Position Monitor
   - Runs every 1-5 minutes during market hours.
   - Checks:
     - open orders
     - filled orders
     - current positions
     - P&L
     - stop/target rules
     - expiration risk
   - Closes or flags positions according to policy.

10. Audit Log / Flight Recorder
   - Store every decision in SQLite/Postgres:
     - timestamp
     - input data snapshot
     - signal values
     - agent proposal
     - critic result
     - risk gate result
     - order payload
     - order response
     - fill status
     - P&L update
   - This becomes the demo superpower.

11. Dashboard
   - First screen should be the live trading cockpit:
     - equity curve
     - P&L
     - open risk
     - active trades
     - latest agent decisions
     - rejected proposals
     - option-chain selected legs
     - risk-gate status
   - Replay mode:
     - click any trade
     - see the market state, agent thesis, risk checks, order, and result

## 7. Tech Stack

Recommended stack:

- Backend: Python + FastAPI
- Trading/data: `alpaca-py`
- Agent orchestration: OpenAI API or local LLM fallback
- Storage: SQLite for speed; Postgres if deploying with a managed DB
- Jobs: APScheduler or simple asyncio loop
- Frontend: React + Vite + TypeScript
- Charts: Recharts or lightweight-charts
- Deployment:
  - Frontend: Vercel/Netlify
  - Backend: Render/Fly/Railway
  - Alternative: single Docker Compose deploy
- Integration proof:
  - Alpaca Trading API for actual order placement
  - Alpaca MCP server for account/data/order tool usage, or Alpaca CLI commands with JSON outputs logged

Fastest reliable path:

- Use `alpaca-py` for app internals.
- Use Alpaca CLI or MCP as a visible "agent tool bridge" and log its outputs.
- This avoids making the whole app depend on an MCP runtime while still satisfying the requirement.

## 8. P&L Strategy For The Contest

The judging includes paper P&L, so we need a pragmatic contest strategy, not just a beautiful app.

Constraints:

- 7-day contest, very short sample.
- Options are volatile.
- Paper fills may be optimistic.
- A strategy that never trades may look safe but loses the P&L category.
- A strategy that yolo-buys far OTM options might win P&L by luck but looks reckless.

Recommended contest posture:

- Risk-seeking but bounded.
- Defined-risk debit spreads and long-volatility trades only.
- No naked short options.
- No unlimited-loss structures.
- Trade 1-5 high-quality setups per day.
- Risk 1.0%-2.0% equity per trade.
- Let P&L be visible, but make judges trust the process even if short-term P&L is noisy.

Candidate trade logic:

Bull call debit spread:

- Underlying in top momentum bucket.
- 5-day trend positive.
- Intraday above VWAP or previous close.
- Volume ratio elevated.
- Buy call around 0.45-0.60 delta.
- Sell call around 0.25-0.35 delta.
- Expiry 7-21 days.
- Profit target: 40%-70% of debit.
- Stop: 40%-60% of debit loss or thesis invalidation.

Bear put debit spread:

- Underlying in bottom momentum bucket.
- 5-day trend negative.
- Intraday below VWAP or previous close.
- Buy put around -0.45 to -0.60 delta.
- Sell put around -0.25 to -0.35 delta.
- Same risk and exit logic.

Long straddle/strangle:

- Only for high expected move or abnormal volume/news.
- Use near-term expiry, but avoid same-day expiry by default.
- Stop if premium decays past threshold.
- Take profit quickly on sharp move.

## 9. MVP Definition

The MVP must be demoable even if the market is closed.

Must have:

- Alpaca paper account configuration.
- Fresh account checklist for final submission.
- Market scanner for 10-20 liquid symbols.
- Option-chain fetcher.
- One working strategy: bull call/bear put debit spread.
- AI proposal generator with strict JSON schema.
- Deterministic risk gate.
- Alpaca order placement in paper mode.
- Order/position monitor.
- SQLite audit log.
- Dashboard with live mode and replay mode.
- README, one-page write-up, deck, video script.

Nice-to-have:

- Multi-agent committee.
- Straddle/strangle mode.
- News-aware catalyst scoring.
- Backtest/replay on historical bars.
- Social-post generator.
- Featherless AI integration for partner tech angle.

Cut if behind:

- Complex portfolio optimization.
- Real-time websockets.
- Too many strategy templates.
- Reinforcement learning.
- Full natural-language chat interface.
- Live-money mode.

## 10. Build Timeline

Current date: Sunday, August 30, 2026.

Hackathon ends: Friday, September 4, 2026.

That leaves roughly 5 days. We need ruthless sequencing.

### Day 1: Foundation And Alpaca Connectivity

Goals:

- Create app structure.
- Set up `.env.example`.
- Connect Alpaca paper account.
- Fetch account, clock, positions, orders.
- Fetch stock bars/snapshots.
- Fetch option contracts/chains.
- Store snapshots in SQLite.

Deliverables:

- Backend starts locally.
- `/health`, `/account`, `/market/snapshot`, `/options/chain/{symbol}` work.
- README has setup steps.

### Day 2: Strategy Engine And Risk Gate

Goals:

- Implement liquid universe scanner.
- Implement bullish/bearish signal scoring.
- Implement debit-spread selector.
- Implement deterministic risk gate.
- Create structured proposal schema.

Deliverables:

- `/agent/propose` returns a valid options trade proposal.
- `/risk/check` returns pass/reject with reasons.
- Unit tests for risk limits and contract filters.

### Day 3: Alpaca Execution And Position Monitoring

Goals:

- Submit paper option orders.
- Track order status.
- Track positions and P&L.
- Add stop/target monitor.
- Persist every action to audit log.

Deliverables:

- One end-to-end paper trade path works.
- Dashboard can show real order IDs and decision history.
- CLI or MCP usage is logged for compliance.

### Day 4: Frontend And Replayable Demo

Goals:

- Build polished cockpit dashboard.
- Build decision replay view.
- Add "demo mode" using recorded/synthetic data for market-closed presentation.
- Add charts and trade cards.

Deliverables:

- Hosted demo candidate.
- Judges can understand the product in less than 60 seconds.
- Demo works during closed market hours.

### Day 5: Submission, P&L Run, Pitch

Goals:

- Create fresh Alpaca paper account with $100,000.
- Run the agent under final account.
- Capture trading activity.
- Record video.
- Finish deck and one-page write-up.
- Post social updates.

Deliverables:

- Public GitHub repo.
- Hosted app URL.
- Paper account ID.
- Video.
- Slides.
- Cover image.
- 3-5 social posts.

## 11. Repo Structure

Suggested structure:

```text
alpaca26/
  README.md
  HACKATHON_WIN_PLAN.md
  .env.example
  backend/
    app/
      main.py
      config.py
      db.py
      alpaca_client.py
      models.py
      routes/
        account.py
        market.py
        options.py
        agent.py
        audit.py
      trading/
        universe.py
        signals.py
        option_selector.py
        risk_gate.py
        executor.py
        monitor.py
      agents/
        analyst.py
        critic.py
        schemas.py
      storage/
        migrations/
    tests/
  frontend/
    src/
      App.tsx
      api/
      components/
      pages/
        Cockpit.tsx
        Replay.tsx
        Settings.tsx
  docs/
    one-page-writeup.md
    pitch-deck-outline.md
    video-script.md
    social-posts.md
```

## 12. Demo Storyboard

The demo should not start with setup. It should start inside the cockpit.

Video flow:

1. "This is FlightDeck Alpha, an autonomous options agent running on Alpaca paper trading."
2. Show live equity/P&L and open risk.
3. Show scanner finding a high-momentum symbol.
4. Show selected options strategy: bull call debit spread or bear put debit spread.
5. Show the AI thesis and evidence.
6. Show critic review.
7. Show deterministic risk gates.
8. Show paper order submission through Alpaca.
9. Show order/position monitor.
10. Show replay: every decision is auditable.
11. Close with submitted paper account P&L and why this matters.

Pitch framing:

- Problem: AI agents can trade, but trading without controls is dangerous and opaque.
- Solution: autonomous options trading with visible reasoning and deterministic risk gates.
- Differentiator: flight-recorder audit trail plus defined-risk options execution.
- Tech: Alpaca Trading API, MCP/CLI, options data, paper execution, AI analyst, critic, risk engine.
- Business value: useful for education, strategy prototyping, compliance-style review, and safer automation research.

## 13. Judging Optimization

P&L Performance:

- Run the agent on final account early enough to accumulate trade history.
- Keep strategy active but bounded.
- Show realized and unrealized P&L.
- Include benchmark comparison against SPY/QQQ for the same period.

Technology Implementation:

- Use Alpaca Trading API for real paper orders.
- Use Alpaca MCP or CLI visibly and log its outputs.
- Use option chain, option snapshots/Greeks, orders, positions, portfolio history.
- Do not fake trading if avoidable.

Creativity and Originality:

- Flight-recorder concept.
- AI critic plus deterministic risk gate.
- Rejected-trade gallery: show restraint, not just action.
- Replayable decisions.

Presentation and Execution:

- Keep the UI dense, operational, and serious.
- Avoid a generic landing page.
- First screen should look like a real trading cockpit.
- Record a crisp demo with both live and replay modes.

Social Engagement:

- Post 3-5 times:
  - Day 1: architecture sketch
  - Day 2: first Alpaca option-chain fetch
  - Day 3: first risk-gated paper order
  - Day 4: cockpit/replay demo clip
  - Day 5: final submission and lessons learned

## 14. Risk Register

Alpaca credentials unavailable:

- Build full demo mode with recorded/mock Alpaca-like data.
- Leave clear `.env.example`.
- Still integrate SDK interfaces so credentials can be added later.

Options order placement issues:

- First implement single-leg long calls/puts as fallback.
- Then add multi-leg debit spreads.
- Use paper account only.

Market closed:

- Replay mode must work from stored snapshots.
- Use mock scenarios for video.

LLM output invalid:

- Enforce JSON schema.
- Reject invalid proposals.
- Use deterministic fallback thesis.

P&L poor:

- Presentation must emphasize process, risk controls, and replay.
- Include risk-adjusted behavior and rejected bad trades.

Too much scope:

- Build one strategy well.
- Dashboard and audit trail matter more than five half-working agents.

## 15. Immediate Next Steps

1. Scaffold backend and frontend.
2. Add Alpaca configuration and account/market endpoints.
3. Implement option-chain fetch and contract filtering.
4. Implement debit-spread proposal generation.
5. Implement risk gate and audit log.
6. Build cockpit dashboard.
7. Add execution and monitor.
8. Create final-account runbook and submission assets.

Recommended first coding target:

Build the backend with Alpaca paper connectivity and a `/propose` endpoint that returns a risk-checked debit spread candidate. Once that works, the rest of the project has a spine.

