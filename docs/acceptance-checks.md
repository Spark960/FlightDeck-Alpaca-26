# Acceptance Checks

Run these checks at regular intervals. If a check fails, fix it before adding scope.

## Every 2 Hours

- [ ] The app still starts locally.
- [ ] The latest endpoint or screen has a clear success state.
- [ ] New code has no obvious secret leakage.
- [ ] The audit log still records the latest agent cycle.
- [ ] We can explain what changed since the last checkpoint.
- [ ] Scope has not expanded without cutting something else.

Pass rule:

- [ ] 5 of 6 checks pass, and any failed check has an owner.

## End Of Each Build Day

- [ ] Current work is committed or at least cleanly resumable.
- [ ] README reflects the current setup.
- [ ] Known blockers are written down.
- [ ] Demo mode still works.
- [ ] Submission tracker is updated.
- [ ] Tomorrow's first task is obvious.

Pass rule:

- [ ] A teammate can resume from the docs without needing a verbal download.

## Alpaca Integration Check

- [ ] Paper mode is clearly enabled.
- [ ] Account endpoint returns paper account info.
- [ ] Clock endpoint returns market status.
- [ ] Orders endpoint returns recent orders.
- [ ] Option contracts can be fetched for `SPY` or `AAPL`.
- [ ] Option chain or snapshots include usable quote data.
- [ ] API errors are logged without crashing the app.

Pass rule:

- [ ] Account, clock, and one options endpoint work with real credentials or demo fallback.

## Strategy Check

- [ ] Scanner can rank symbols.
- [ ] Strategy selector can produce bull call spread.
- [ ] Strategy selector can produce bear put spread.
- [ ] Strategy selector can reject bad/missing chains.
- [ ] Proposal includes max loss.
- [ ] Proposal includes entry and exit logic.
- [ ] Proposal includes evidence and invalidation.

Pass rule:

- [ ] At least one valid trade candidate and one rejected candidate can be shown.

## Risk Gate Check

- [ ] Oversized trade is rejected.
- [ ] Unsupported strategy is rejected.
- [ ] Stale quote is rejected.
- [ ] Wide bid/ask spread is rejected.
- [ ] Live-trading mode is rejected.
- [ ] Valid small defined-risk spread is approved.
- [ ] Every decision includes reasons.

Pass rule:

- [ ] All rejection tests pass before any paper order submission.

## Execution Check

- [ ] Dry-run order payload is correct.
- [ ] Client order ID is unique.
- [ ] Approved proposal links to risk check.
- [ ] Paper order submission works.
- [ ] Alpaca order ID is persisted.
- [ ] Order status can be refreshed.
- [ ] Rejected orders are handled gracefully.

Pass rule:

- [ ] A paper order can be traced from scan to proposal to risk check to Alpaca response.

## Monitoring Check

- [ ] Open positions are visible.
- [ ] Open orders are visible.
- [ ] P&L updates.
- [ ] Stop-loss condition can be simulated.
- [ ] Take-profit condition can be simulated.
- [ ] Time-stop condition can be simulated.
- [ ] Monitor does not double-submit close orders.

Pass rule:

- [ ] Monitor loop can run three times without duplicate or corrupt events.

## Dashboard Check

- [ ] Cockpit first screen is not empty.
- [ ] Key metrics are visible without scrolling on desktop.
- [ ] Latest agent decision is visible.
- [ ] Risk-gate result is visible.
- [ ] Replay view reconstructs one full run.
- [ ] Demo mode works without credentials.
- [ ] Mobile layout has no severe overlap.

Pass rule:

- [ ] A judge can understand signal, risk, and execution from the UI alone.

## Submission Readiness Check

- [ ] Public GitHub repo exists.
- [ ] Hosted app URL works.
- [ ] Video exists.
- [ ] Slide deck exists.
- [ ] One-page write-up exists.
- [ ] Cover image exists.
- [ ] Alpaca paper account ID is ready.
- [ ] Social links are ready or intentionally omitted.

Pass rule:

- [ ] No hard hackathon requirement is missing.

