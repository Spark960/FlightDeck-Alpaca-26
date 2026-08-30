# Phase Checklists

Use this file during implementation. Check items as they land.

## Phase 0: Scope Lock

- [x] Product name finalized.
- [x] One-liner finalized.
- [x] Primary strategy finalized.
- [x] Fallback strategy finalized.
- [x] Tech stack finalized.
- [x] README stub created.
- [x] `.env.example` created.
- [x] Demo mode requirement accepted.

Checkpoint:

- [x] We can start coding without redesigning the product.

## Phase 1: Alpaca Connectivity

- [x] Backend project created.
- [x] Settings loader created.
- [x] Alpaca keys loaded from environment.
- [x] Paper mode defaults to true.
- [x] Account endpoint works.
- [x] Clock endpoint works.
- [x] Positions endpoint works.
- [x] Orders endpoint works.
- [x] Stock snapshot endpoint works.
- [x] Options contracts endpoint works.
- [x] Options chain endpoint works.
- [x] Missing credentials return helpful errors.

Checkpoint:

- [ ] We can prove Alpaca integration in a screen recording.

## Phase 2: Persistence And Audit

- [x] SQLite connection created.
- [x] Schema created.
- [x] Agent run table created.
- [x] Market snapshots persisted.
- [x] Proposals persisted.
- [ ] Risk checks persisted.
- [ ] Orders persisted.
- [x] Position snapshots persisted.
- [x] Audit list endpoint created.
- [x] Audit detail endpoint created.

Checkpoint:

- [ ] One agent run can be replayed from database records.

## Phase 3: Market Scanner

- [x] Liquid universe defined.
- [ ] Historical bars fetched.
- [x] Current quotes/snapshots fetched.
- [ ] 1-day return computed.
- [ ] 5-day return computed.
- [ ] Volume ratio computed.
- [ ] Moving-average slope computed.
- [ ] Volatility proxy computed.
- [x] Bullish score computed.
- [x] Bearish score computed.
- [x] Candidates ranked.
- [x] No-trade state supported.

Checkpoint:

- [ ] Scanner produces ranked candidates with reason codes.

## Phase 4: Options Selector

- [x] Option-chain fetch integrated.
- [x] Expiration filter implemented.
- [x] Tradable contract filter implemented.
- [x] Bid/ask spread filter implemented.
- [ ] Quote freshness filter implemented.
- [ ] Open interest filter implemented if available.
- [x] Bull call spread selector implemented.
- [x] Bear put spread selector implemented.
- [ ] Single-leg fallback implemented.
- [x] Max loss calculated.
- [x] Max profit calculated where possible.
- [x] Break-even calculated where possible.
- [ ] Greeks surfaced where available.

Checkpoint:

- [ ] A valid options trade candidate can be generated from a scan result.

## Phase 5: AI Analyst And Critic

- [ ] Proposal JSON schema defined.
- [ ] Analyst prompt created.
- [ ] Analyst output validated.
- [ ] Invalid output logged.
- [ ] Critic prompt created.
- [ ] Critic output validated.
- [ ] Critic can pass proposal.
- [ ] Critic can reject weak proposal.
- [ ] Proposal detail endpoint created.

Checkpoint:

- [ ] The agent can explain a trade without being allowed to execute it.

## Phase 6: Risk Gate

- [ ] Paper-only check implemented.
- [ ] Account equity check implemented.
- [ ] Buying-power check implemented.
- [ ] Market-open check implemented.
- [ ] End-of-day cutoff implemented.
- [ ] Max risk per trade implemented.
- [ ] Max daily loss implemented.
- [ ] Max drawdown implemented.
- [ ] Max open trades implemented.
- [ ] Max same-underlying exposure implemented.
- [ ] Max premium deployed implemented.
- [ ] No naked short option check implemented.
- [ ] Unsupported strategy rejection implemented.
- [ ] Unit tests added.

Checkpoint:

- [ ] No trade can reach execution without risk approval.

## Phase 7: Execution

- [ ] Order payload builder created.
- [ ] Limit price near midpoint implemented.
- [ ] Client order ID implemented.
- [ ] Dry-run endpoint implemented.
- [ ] Paper order submit implemented.
- [ ] Alpaca response persisted.
- [ ] Order status polling implemented.
- [ ] Rejection handling implemented.
- [ ] Partial-fill handling implemented.
- [ ] MCP or CLI proof path implemented.

Checkpoint:

- [ ] We can submit a paper options order and link it to the original proposal.

## Phase 8: Position Monitor

- [ ] Monitor loop created.
- [ ] Position polling implemented.
- [ ] Order polling implemented.
- [ ] Fill polling implemented.
- [ ] P&L update implemented.
- [ ] Take-profit rule implemented.
- [ ] Stop-loss rule implemented.
- [ ] Time-stop rule implemented.
- [ ] Expiration-risk rule implemented.
- [ ] Duplicate-action prevention implemented.
- [ ] Monitor events persisted.

Checkpoint:

- [ ] The system can explain whether each position should be held, closed, or watched.

## Phase 9: Frontend

- [ ] React/Vite app created.
- [ ] API client created.
- [ ] Cockpit page built.
- [ ] Replay page built.
- [ ] Positions page built.
- [ ] Risk console built.
- [ ] Settings page built.
- [ ] Demo mode data wired.
- [ ] Loading states added.
- [ ] Empty states added.
- [ ] Error states added.
- [ ] Mobile layout checked.
- [ ] Desktop layout checked.

Checkpoint:

- [ ] The demo can be understood without a narrator.

## Phase 10: Deployment

- [ ] Backend deployment chosen.
- [ ] Frontend deployment chosen.
- [ ] Environment variables configured.
- [ ] Backend deployed.
- [ ] Frontend deployed.
- [ ] Public smoke test passes.
- [ ] Secrets not exposed.
- [ ] Demo mode works on public URL.

Checkpoint:

- [ ] Hosted app URL is submission-ready.

## Phase 11: Final Account Run

- [ ] Fresh Alpaca paper account created.
- [ ] Starting balance confirmed as $100,000.
- [ ] Account ID recorded privately.
- [ ] Paper API keys generated.
- [ ] Final account connected.
- [ ] First account check recorded.
- [ ] First scan recorded.
- [ ] First dry-run recorded.
- [ ] First paper trade submitted.
- [ ] Trading activity visible in Alpaca.
- [ ] P&L screenshot/evidence captured.

Checkpoint:

- [ ] The submitted account has eligible paper trading activity.

## Phase 12: Submission

- [ ] Public GitHub repo ready.
- [ ] Hosted app URL ready.
- [ ] Project title ready.
- [ ] Short description ready.
- [ ] Long description ready.
- [ ] Tags ready.
- [ ] Cover image ready.
- [ ] Video ready.
- [ ] Slide deck ready.
- [ ] One-page write-up ready.
- [ ] Alpaca account ID ready.
- [ ] Social post links ready.

Checkpoint:

- [ ] Submission can be uploaded without missing assets.
