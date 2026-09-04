# FlightDeck Alpha — Backtesting Guide

Backtesting for this project is **not** a separate "run the strategy on history" mode. The codebase is built for live, paper-trading autonomy, and the cleanest path to a credible backtest is to **reuse the existing domain code against historical Alpaca market and option data**, then compare the result to the live paper-trading P&L. This document specifies exactly how to do that without forking the project.

## Why this shape

The whole point of the architecture is that deterministic code owns money. To preserve that property, a backtest must call the same `signals.rank_candidates`, `option_selector.select_debit_spread`, and `trading.risk.evaluate_risk` modules the live agent uses. The only thing that changes is the **data source**: instead of `AlpacaGateway` calling live `/v2/...` endpoints, a backtest gateway calls historical bars and a frozen option-chain snapshot.

The "flight recorder" audit log makes the comparison meaningful: every backtest run gets the same `run_id` shape, the same `risk_checks` table, and the same `orders` table the live agent uses, so we can diff them later.

## Backtesting data model

We need three data products for a backtest over date range `[D0, D1]` with bar size `1 day`:

1. **Stock daily bars** for the universe — open, high, low, close, volume. Source: `AlpacaGateway.stock_bars()` already supports this with a 30-day limit; a backtest gateway must extend to 5+ years.
2. **Option chains and snapshots per underlying per day** — strike list, expiration date, greeks, bid/ask, open interest, latest quote timestamp. Source: `AlpacaGateway.option_contracts()` and `option_chain()`. For historical backtests, the historical option-data API (`/v1beta1/options/bars`) is the canonical source.
3. **Account state per day** — for the risk gate. Backtests must simulate equity, buying power, daily P&L, and drawdown themselves, because there is no live `account()` endpoint in the past.

The store stays `flightdeck_alpha.db` with a separate `BACKTEST_MODE=true` flag in `config.py` so the same `app.db` schema is reused. We add a new `audit_run_type` of `backtest` so the Replay page can render backtest runs alongside live ones.

## Backtest gateway (new file)

Create `backend/app/backtest/gateway.py`. It mirrors `AlpacaClient` but is driven by a local `MarketDataStore` that lazily downloads and caches history.

```python
# backend/app/backtest/gateway.py  (sketch)
from dataclasses import dataclass
from datetime import date

from app.config import Settings
from app.backtest.store import MarketDataStore


class BacktestGateway:
    def __init__(self, settings: Settings, store: MarketDataStore, day: date) -> None:
        self.settings = settings
        self.store = store
        self.day = day

    def account(self) -> dict:
        return self.store.account_on(self.day)

    def clock(self) -> dict:
        return {"is_open": True, "next_close": f"{self.day}T20:00:00Z"}

    def positions(self) -> list[dict]:
        return self.store.positions_on(self.day)

    def orders(self) -> list[dict]:
        return self.store.orders_on(self.day)

    def stock_snapshots(self, symbols: list[str]) -> dict:
        return {s: self.store.stock_snapshot_on(s, self.day) for s in symbols}

    def stock_bars(self, symbols: list[str], days: int = 30) -> dict:
        return {s: self.store.stock_bars_window(s, self.day, days) for s in symbols}

    def option_contracts(self, symbol: str) -> dict:
        return {"option_contracts": self.store.option_contracts_on(symbol, self.day)}

    def option_chain(self, symbol: str) -> dict:
        return self.store.option_chain_on(symbol, self.day)

    def submit_order(self, payload: dict) -> dict:
        return self.store.simulate_fill(payload, as_of=self.day)
```

The crucial method is `submit_order`: it must model a **limit-order fill at the midpoint of the bid/ask at the bar's close**, the same way `trading.order_builder._net_debit_limit` already prices entry. Anything more sophisticated (queue position, partial fills) is out of scope for the hackathon, but the call site stays identical.

## Market data store (new file)

`backend/app/backtest/store.py` is a thin layer over a CSV or parquet cache. The structure below is enough to drive the existing engines.

```text
data/
  stocks/
    SPY/
      2024-01-02.parquet     # columns: open, high, low, close, volume
      2024-01-03.parquet
      ...
  options/
    SPY/
      2024-01-02/
        contracts.parquet     # columns: symbol, type, strike, expiration, tradable
        chain.parquet         # columns: contract_symbol, bid, ask, delta, open_interest, t
```

Loading order (one-time per backtest run):

1. Use `alpaca.data.requests.StockBarsRequest(timeframe=TimeFrame.Day, start=D0, end=D1, adjustment=Adjustment.ALL)` to download stock bars for `LIQUID_UNIVERSE`.
2. For each trading day in the range, request the option chain from `data.alpaca.markets/v1beta1/options/snapshots/SPY?feed=indicative&limit=1000` and persist the rows. Alpaca historical options data is part of the paid market-data subscription but is available on most paper accounts.
3. Build an account simulator: equity = 100_000, no margin, P&L = sum of closed trade mark-to-market on the day.

## Running a backtest

A new route `POST /api/backtest/run` reuses the existing flow. It is a thin orchestrator that, for each day in the range, calls the same endpoints a live cycle would call:

```python
# backend/app/backtest/runner.py
from datetime import date, timedelta
from app.config import get_settings
from app.backtest.gateway import BacktestGateway
from app.backtest.store import MarketDataStore
from app.trading.signals import rank_candidates
from app.trading.option_selector import select_debit_spread
from app.trading.risk import evaluate_risk
from app.trading.monitor import run_monitor
from app.storage.audit import create_run, complete_run, record_trade_proposal, record_risk_check, record_order
from app.trading.order_builder import build_order_payload


def run_backtest(start: date, end: date) -> dict:
    settings = get_settings()
    store = MarketDataStore(root="./data", start=start, end=end)
    run_id = create_run("backtest", {"start": str(start), "end": str(end)})

    equity = 100_000.0
    closed: list[dict] = []
    open_positions: list[dict] = []

    for d in daterange(start, end):
        gw = BacktestGateway(settings, store, d)
        # 1. scan
        candidates = rank_candidates(gw.stock_snapshots(LIQUID_UNIVERSE), gw.stock_bars(LIQUID_UNIVERSE))
        # 2. propose
        for c in candidates[:3]:
            contracts = gw.option_contracts(c["symbol"])
            chain = gw.option_chain(c["symbol"])
            proposal = select_debit_spread(
                symbol=c["symbol"], direction=c["direction"],
                contracts_payload=contracts, chain_payload=chain,
                max_debit=max_debit_for_equity(equity),
            )
            if not proposal["accepted"]:
                continue
            # 3. risk
            risk = evaluate_risk(proposal, gw.account(), gw.clock(), open_positions, settings)
            if not risk["approved"]:
                continue
            # 4. submit
            order = gw.submit_order(build_order_payload(proposal, f"BT-{d}-{c['symbol']}"))
            open_positions.append({"proposal": proposal, "entry_cost": order["filled_avg_price"]})
        # 5. monitor at end of day
        result = run_monitor(gw.account(), open_positions, [], {}, settings)
        # mark to market and close any that hit a rule
        open_positions = [p for p in open_positions if not _should_close(result, p)]

    complete_run(run_id, {"closed_trades": closed, "final_equity": equity})
    return {"run_id": run_id, "closed": closed, "final_equity": equity}
```

Three details to keep the backtest honest:

- The selector and risk-gate calls are the **same** function references the live routes use. Any future code change to the live agent's policy automatically propagates to the backtest. This is the single most important property of the design.
- `max_debit` for the backtest is sized off the **simulated equity** at the start of each day, not a fixed $1500. This is what `risk.evaluate_risk` already does internally, but the caller must pass the day's `account()` snapshot.
- The risk gate enforces a hard `ALPACA_PAPER=true` check. A backtest must spoof this by setting `paper=True` on the `Settings` dataclass even though no network call happens, otherwise `paper_trading_required` will be a blocking reason on every proposal.

## Walk-forward vs single-shot

For the hackathon, a **single in-sample run** (e.g. 2024-01-02 -> 2024-12-31) is enough to show that the strategy has edge. For rigor, run a **walk-forward**:

- 1-year train, 3-month test, slide forward 3 months.
- Report the equity curve and a small stat block: CAGR, max drawdown, win rate, average win/loss, profit factor.
- Compare against `SPY` buy-and-hold over the same window.

Walk-forward results are far more defensible than a single period because they test whether the policy generalizes, not just whether it once worked.

## Reporting a backtest

Add a `BACKTEST_REPORT.md` next to this file with:

- Date range, universe, starting equity, ending equity.
- Per-day stats: number of proposals, number approved, number rejected (with `blocking_reasons` breakdown), number of fills.
- Equity curve as a small CSV; load into a notebook to plot.
- Side-by-side: backtest final equity vs live paper-trading final equity at submission time.

The point of doing this is **not** to claim the backtest predicts the future. The point is to show judges that the deterministic risk gates and the selector together produce sane, explainable, bounded behavior on real data, not only on demo data.

## Limitations to disclose

- The hackathon will be judged partly on **live P&L**, not backtest. Backtest is supporting evidence, not the headline.
- Historical option data on Alpaca is snapshot-based; bid/ask history is sparse. Fill simulation at midpoint is a reasonable default but is not what the live market actually produces.
- Slippage, queue position, partial fills, fees, and dividends are not modeled. None of these matter for paper-trading, but they would matter for live.
- The scanner uses intraday quote freshness as a feature. Historical intraday quote timestamps exist on Alpaca but are noisy. A backtest that scores the freshness check at the bar's close rather than at "now" is more honest.

## What the hackathon judges actually want

They want to see that the same engine that trades on the fresh $100k paper account has been **run on history without code forking**. A small equity-curve plot plus a one-paragraph write-up of the walk-forward result is enough to clear that bar. Anything more is over-engineering for a 7-day build.
