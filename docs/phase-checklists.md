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
- [x] Risk checks persisted.
- [ ] Orders persisted.
- [x] Position snapshots persisted.
- [x] Audit list endpoint created.
- [x] Audit detail endpoint created.

Checkpoint:

- [ ] One agent run can be replayed from database records.

## Phase 3: Market Scanner

- [x] Liquid universe defined.
- [x] Historical bars fetched.
- [x] Current quotes/snapshots fetched.
- [x] 1-day return computed.
- [x] 5-day return computed.
- [x] Volume ratio computed.
- [x] Moving-average slope computed.
- [x] Volatility proxy computed.
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
- [x] Quote freshness filter implemented.
- [x] Open interest filter implemented if available.
- [x] Bull call spread selector implemented.
- [x] Bear put spread selector implemented.
- [x] Single-leg fallback implemented.
- [x] Max loss calculated.
- [x] Max profit calculated where possible.
- [x] Break-even calculated where possible.
- [x] Greeks surfaced where available.

Checkpoint:

- [ ] A valid options trade candidate can be generated from a scan result.

## Phase 5: AI Analyst And Critic

- [x] Proposal JSON schema defined.
- [x] Analyst prompt created.
- [x] Analyst output validated.
- [x] Invalid output logged.
- [x] Critic prompt created.
- [x] Critic output validated.
- [x] Critic can pass proposal.
- [x] Critic can reject weak proposal.
- [x] Proposal detail endpoint created.

Checkpoint:

- [ ] The agent can explain a trade without being allowed to execute it.

## Phase 6: Risk Gate

- [x] Paper-only check implemented.
- [x] Account equity check implemented.
- [x] Buying-power check implemented.
- [x] Market-open check implemented.
- [x] End-of-day cutoff implemented.
- [x] Max risk per trade implemented.
- [x] Max daily loss implemented.
- [x] Max drawdown implemented.
- [x] Max open trades implemented.
- [x] Max same-underlying exposure implemented.
- [x] Max premium deployed implemented.
- [x] No naked short option check implemented.
- [x] Unsupported strategy rejection implemented.
- [x] Unit tests added.

Checkpoint:

- [ ] No trade can reach execution without risk approval.

## Phase 7: Execution

- [x] Order payload builder created.
- [x] Limit price near midpoint implemented.
- [x] Client order ID implemented.
- [x] Dry-run endpoint implemented.
- [x] Paper order submit implemented.
- [x] Alpaca response persisted.
- [x] Order status polling implemented.
- [x] Rejection handling implemented.
- [x] Partial-fill handling implemented.
- [ ] MCP or CLI proof path implemented.

Checkpoint:

- [x] We can submit a paper options order and link it to the original proposal.

## Phase 8: Position Monitor

- [x] Monitor loop created.
- [x] Position polling implemented.
- [x] Order polling implemented.
- [x] Fill polling implemented.
- [x] P&L update implemented.
- [x] Take-profit rule implemented.
- [x] Stop-loss rule implemented.
- [x] Time-stop rule implemented.
- [x] Expiration-risk rule implemented.
- [x] Duplicate-action prevention implemented.
- [x] Monitor events persisted.

Checkpoint:

- [x] The system can explain whether each position should be held, closed, or watched.

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
