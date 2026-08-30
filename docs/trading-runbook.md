# Trading Runbook

This is the operating procedure for running FlightDeck Alpha during the hackathon.

## Non-Negotiables

- [ ] Use Alpaca paper trading only.
- [ ] Never paste API secrets into chat, docs, GitHub, screenshots, or video.
- [ ] Use a fresh final paper account for judging.
- [ ] Confirm the final account starts at $100,000.
- [ ] Do not enable live trading.
- [ ] Do not allow naked short options.
- [ ] Do not submit orders unless risk gate approves them.

## Pre-Market Checklist

Run before the market opens or before the first agent cycle.

- [ ] Backend starts.
- [ ] Frontend starts.
- [ ] Database is reachable.
- [ ] Alpaca credentials are loaded.
- [ ] Account endpoint confirms paper account.
- [ ] Account equity and buying power are visible.
- [ ] Clock endpoint returns market status.
- [ ] Existing positions are loaded.
- [ ] Existing open orders are loaded.
- [ ] Daily loss state is initialized.
- [ ] Demo mode is available as fallback.

Decision:

- [ ] If Alpaca is unavailable, run demo mode and do not submit trades.
- [ ] If account is not the final fresh paper account, do not use it for final judging P&L.
- [ ] If paper mode is not confirmed, stop immediately.

## Market-Open Cycle

Run every 15-30 minutes, or manually while building.

1. Scan universe.

- [ ] Pull current market data.
- [ ] Pull historical bars.
- [ ] Compute features.
- [ ] Rank symbols.
- [ ] Persist scan result.

2. Select options candidate.

- [ ] Fetch option chain for top candidates.
- [ ] Filter expirations.
- [ ] Filter bid/ask spreads.
- [ ] Filter tradability.
- [ ] Select debit spread or fallback long option.
- [ ] Persist selected contracts.

3. Generate proposal.

- [ ] Analyst produces JSON.
- [ ] JSON schema validates.
- [ ] Critic reviews proposal.
- [ ] Proposal is persisted.

4. Risk check.

- [ ] Run deterministic risk gate.
- [ ] Persist risk result.
- [ ] If rejected, stop and show reason.
- [ ] If approved, continue.

5. Execute or dry-run.

- [ ] Build order payload.
- [ ] Check idempotency/client order ID.
- [ ] Submit dry-run first while testing.
- [ ] Submit paper order only when ready.
- [ ] Persist Alpaca response.

6. Monitor.

- [ ] Refresh orders.
- [ ] Refresh positions.
- [ ] Refresh P&L.
- [ ] Check exits.
- [ ] Persist monitor event.

## New Trade Decision Rules

Approve only when all are true:

- [ ] Strategy is defined-risk.
- [ ] Max loss is known.
- [ ] Risk per trade is within budget.
- [ ] Option quote is fresh.
- [ ] Bid/ask spread is acceptable.
- [ ] Contract expiration is acceptable.
- [ ] Open-trade limit is not exceeded.
- [ ] Same-underlying limit is not exceeded.
- [ ] Daily drawdown halt is not active.
- [ ] Critic did not reject proposal.

Reject when any are true:

- [ ] Missing max loss.
- [ ] Missing leg prices.
- [ ] Wide option spread.
- [ ] Stale market data.
- [ ] Unsupported strategy.
- [ ] Naked short option exposure.
- [ ] Too close to expiration.
- [ ] Too close to market close for new entry.
- [ ] Account mode is uncertain.
- [ ] Alpaca returns inconsistent position/order state.

## Position Management Rules

For debit spreads:

- [ ] Take profit when spread value gains 40%-70% versus entry debit.
- [ ] Stop loss when spread value loses 40%-60% versus entry debit.
- [ ] Close if thesis invalidation triggers.
- [ ] Close before expiration-risk window.
- [ ] Do not add to losers automatically.
- [ ] Do not roll positions unless explicitly implemented and risk checked.

For single-leg fallback:

- [ ] Use smaller risk budget.
- [ ] Take profit quickly on sharp moves.
- [ ] Stop on premium decay.
- [ ] Avoid holding into expiration.

## Emergency Stops

Stop new trading when:

- [ ] Daily drawdown reaches 3%.
- [ ] Total drawdown reaches 8%.
- [ ] Open order state is inconsistent.
- [ ] Alpaca API repeatedly errors.
- [ ] Database logging fails.
- [ ] Paper mode cannot be confirmed.
- [ ] Option chain data is stale or missing.

Actions:

- [ ] Cancel pending entry orders if they are unsafe or stale.
- [ ] Do not close all positions automatically unless that behavior is intentionally implemented and tested.
- [ ] Record incident in audit log.
- [ ] Switch dashboard to risk-halted state.

## End-Of-Day Checklist

- [ ] Refresh final account equity.
- [ ] Refresh positions.
- [ ] Refresh closed orders.
- [ ] Persist portfolio snapshot.
- [ ] Export key audit events.
- [ ] Capture dashboard screenshot if useful.
- [ ] Write down P&L, trades placed, and issues.
- [ ] Update submission tracker.

## Evidence To Capture

- [ ] Alpaca paper account ID.
- [ ] Starting balance screenshot or account endpoint result.
- [ ] Order IDs.
- [ ] Position/P&L snapshot.
- [ ] Audit replay screenshot.
- [ ] Risk-gate rejection screenshot.
- [ ] MCP or CLI output proof.

