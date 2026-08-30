from datetime import UTC, datetime, timedelta
from typing import Any


def _now() -> datetime:
    return datetime.now(tz=UTC)


def demo_account() -> dict[str, Any]:
    return {
        "id": "PAPER-DEMO-ACCOUNT",
        "account_number": "FDA-DEMO",
        "status": "ACTIVE",
        "currency": "USD",
        "cash": "100000.00",
        "portfolio_value": "100000.00",
        "buying_power": "200000.00",
        "equity": "100000.00",
        "paper": True,
        "source": "demo",
    }


def demo_clock() -> dict[str, Any]:
    now = _now()
    return {
        "timestamp": now.isoformat(),
        "is_open": False,
        "next_open": (now + timedelta(hours=14)).isoformat(),
        "next_close": (now + timedelta(hours=20, minutes=30)).isoformat(),
        "source": "demo",
    }


def demo_positions() -> list[dict[str, Any]]:
    return [
        {
            "symbol": "SPY260918C00600000",
            "qty": "1",
            "market_value": "540.00",
            "cost_basis": "510.00",
            "unrealized_pl": "30.00",
            "asset_class": "us_option",
            "source": "demo",
        }
    ]


def demo_orders() -> list[dict[str, Any]]:
    return [
        {
            "id": "demo-order-001",
            "client_order_id": "FDA-DEMO-SPY-001",
            "symbol": "SPY260918C00600000",
            "qty": "1",
            "side": "buy",
            "type": "limit",
            "limit_price": "5.10",
            "status": "filled",
            "submitted_at": (_now() - timedelta(minutes=35)).isoformat(),
            "source": "demo",
        }
    ]


def demo_stock_snapshots(symbols: list[str]) -> dict[str, Any]:
    base_prices = {
        "SPY": 640.25,
        "QQQ": 575.4,
        "AAPL": 226.1,
        "MSFT": 511.8,
        "NVDA": 183.6,
    }
    return {
        symbol: {
            "latest_trade": {"price": base_prices.get(symbol, 100.0), "timestamp": _now().isoformat()},
            "latest_quote": {
                "bid_price": round(base_prices.get(symbol, 100.0) - 0.02, 2),
                "ask_price": round(base_prices.get(symbol, 100.0) + 0.02, 2),
                "timestamp": _now().isoformat(),
            },
            "minute_bar": {"volume": 125000, "close": base_prices.get(symbol, 100.0)},
            "daily_bar": {"open": base_prices.get(symbol, 100.0) - 2.5, "close": base_prices.get(symbol, 100.0)},
            "source": "demo",
        }
        for symbol in symbols
    }


def demo_stock_bars(symbols: list[str], days: int = 30) -> dict[str, list[dict[str, Any]]]:
    base_prices = {
        "SPY": 640.25,
        "QQQ": 575.4,
        "AAPL": 226.1,
        "MSFT": 511.8,
        "NVDA": 183.6,
    }
    bars: dict[str, list[dict[str, Any]]] = {}
    for symbol in symbols:
        price = base_prices.get(symbol, 100.0)
        rows = []
        for offset in range(days, 0, -1):
            day = _now() - timedelta(days=offset)
            close = price - (offset * 0.42)
            open_price = close - 0.25
            rows.append(
                {
                    "timestamp": day.isoformat(),
                    "open": round(open_price, 2),
                    "high": round(close + 1.1, 2),
                    "low": round(open_price - 0.8, 2),
                    "close": round(close, 2),
                    "volume": 65_000_000 - offset * 350_000,
                    "source": "demo",
                }
            )
        bars[symbol] = rows
    return bars


def demo_option_contracts(symbol: str) -> dict[str, Any]:
    expiration = (_now() + timedelta(days=19)).date().isoformat()
    return {
        "underlying_symbol": symbol,
        "contracts": [
            {
                "symbol": f"{symbol}260918C00640000",
                "name": f"{symbol} 2026-09-18 640 Call",
                "type": "call",
                "strike_price": "640",
                "expiration_date": expiration,
                "tradable": True,
                "open_interest": 4200,
                "source": "demo",
            },
            {
                "symbol": f"{symbol}260918C00645000",
                "name": f"{symbol} 2026-09-18 645 Call",
                "type": "call",
                "strike_price": "645",
                "expiration_date": expiration,
                "tradable": True,
                "open_interest": 3900,
                "source": "demo",
            },
        ],
        "source": "demo",
    }


def demo_submit_order(payload: dict[str, Any]) -> dict[str, Any]:
    symbol = payload.get("symbol")
    if not symbol and payload.get("legs"):
        symbol = payload["legs"][0]["symbol"]
    return {
        "id": "demo-order-submit-001",
        "client_order_id": payload.get("client_order_id", "FDA-DEMO-ORDER"),
        "symbol": symbol,
        "qty": str(payload.get("qty", 1)),
        "type": payload.get("type", "limit"),
        "limit_price": str(payload.get("limit_price", "0")),
        "status": "accepted",
        "submitted_at": _now().isoformat(),
        "order_class": payload.get("order_class", "simple"),
        "source": "demo",
    }


def demo_option_chain(symbol: str) -> dict[str, Any]:
    expiration = (_now() + timedelta(days=19)).date().isoformat()
    return {
        "underlying_symbol": symbol,
        "expiration": expiration,
        "contracts": [
            {
                "symbol": f"{symbol}260918C00640000",
                "type": "call",
                "strike": 640,
                "bid": 5.0,
                "ask": 5.2,
                "mid": 5.1,
                "delta": 0.52,
                "open_interest": 4200,
                "quote_timestamp": _now().isoformat(),
                "tradable": True,
                "source": "demo",
            },
            {
                "symbol": f"{symbol}260918C00645000",
                "type": "call",
                "strike": 645,
                "bid": 2.45,
                "ask": 2.6,
                "mid": 2.525,
                "delta": 0.31,
                "open_interest": 3900,
                "quote_timestamp": _now().isoformat(),
                "tradable": True,
                "source": "demo",
            },
        ],
        "source": "demo",
    }
