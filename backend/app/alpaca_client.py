from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from app.config import Settings
from app.demo_data import (
    demo_account,
    demo_clock,
    demo_option_chain,
    demo_option_contracts,
    demo_orders,
    demo_positions,
    demo_stock_bars,
    demo_stock_snapshots,
    demo_submit_order,
)


class AlpacaCredentialError(RuntimeError):
    """Raised when live Alpaca data was requested without credentials."""


class AlpacaGateway:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._trading_client: Any | None = None
        self._stock_client: Any | None = None
        self._option_client: Any | None = None

    def account(self) -> dict[str, Any]:
        return self._with_trading_client(lambda client: _model_dump(client.get_account()), demo_account)

    def clock(self) -> dict[str, Any]:
        return self._with_trading_client(lambda client: _model_dump(client.get_clock()), demo_clock)

    def positions(self) -> list[dict[str, Any]]:
        return self._with_trading_client(
            lambda client: [_model_dump(position) for position in client.get_all_positions()],
            demo_positions,
        )

    def orders(self) -> list[dict[str, Any]]:
        return self._with_trading_client(
            lambda client: [_model_dump(order) for order in client.get_orders()],
            demo_orders,
        )

    def stock_snapshots(self, symbols: list[str]) -> dict[str, Any]:
        if self.settings.demo_mode:
            return demo_stock_snapshots(symbols)
        if not self.settings.has_alpaca_credentials:
            raise AlpacaCredentialError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY to use Alpaca.")

        from alpaca.data.requests import StockSnapshotRequest

        client = self._get_stock_client()
        snapshots = client.get_stock_snapshot(StockSnapshotRequest(symbol_or_symbols=symbols))
        return {symbol: _model_dump(snapshot) for symbol, snapshot in snapshots.items()}

    def stock_bars(self, symbols: list[str], days: int = 30) -> dict[str, list[dict[str, Any]]]:
        if self.settings.demo_mode:
            return demo_stock_bars(symbols, days=days)
        if not self.settings.has_alpaca_credentials:
            raise AlpacaCredentialError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY to use Alpaca.")

        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame

        client = self._get_stock_client()
        bars = client.get_stock_bars(
            StockBarsRequest(
                symbol_or_symbols=symbols,
                timeframe=TimeFrame.Day,
                limit=days,
            )
        )
        raw = _model_dump(bars).get("data", {})
        if isinstance(raw, dict):
            return {symbol: [_model_dump(row) for row in rows] for symbol, rows in raw.items()}
        return {}

    def option_contracts(self, symbol: str) -> dict[str, Any]:
        if self.settings.demo_mode:
            return demo_option_contracts(symbol)
        if not self.settings.has_alpaca_credentials:
            raise AlpacaCredentialError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY to use Alpaca.")

        from alpaca.trading.requests import GetOptionContractsRequest

        start, end = _option_expiration_window()
        client = self._get_trading_client()
        contracts: list[dict[str, Any]] = []
        page_token: str | None = None
        for _ in range(10):
            payload = _model_dump(
                client.get_option_contracts(
                    GetOptionContractsRequest(
                        underlying_symbols=[symbol],
                        expiration_date_gte=start,
                        expiration_date_lte=end,
                        limit=1000,
                        page_token=page_token,
                    )
                )
            )
            batch = payload.get("option_contracts") or payload.get("contracts") or []
            contracts.extend(batch)
            page_token = payload.get("next_page_token")
            if not page_token:
                break
        return {"option_contracts": contracts, "next_page_token": page_token}

    def submit_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        if self.settings.demo_mode:
            return demo_submit_order(payload)
        if not self.settings.has_alpaca_credentials:
            raise AlpacaCredentialError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY to use Alpaca.")
        return _model_dump(self._get_trading_client().submit_order(_build_order_request(payload)))

    def get_order(self, order_id: str) -> dict[str, Any]:
        if self.settings.demo_mode:
            for order in demo_orders():
                if order.get("id") == order_id:
                    return order
            return {"id": order_id, "status": "accepted", "source": "demo"}
        if not self.settings.has_alpaca_credentials:
            raise AlpacaCredentialError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY to use Alpaca.")
        return _model_dump(self._get_trading_client().get_order_by_id(order_id))

    def option_chain(self, symbol: str) -> dict[str, Any]:
        if self.settings.demo_mode:
            return demo_option_chain(symbol)
        if not self.settings.has_alpaca_credentials:
            raise AlpacaCredentialError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY to use Alpaca.")

        from alpaca.data.requests import OptionChainRequest

        start, end = _option_expiration_window()
        client = self._get_option_client()
        chain = client.get_option_chain(
            OptionChainRequest(
                underlying_symbol=symbol,
                expiration_date_gte=start,
                expiration_date_lte=end,
            )
        )
        return {contract: _model_dump(snapshot) for contract, snapshot in chain.items()}

    def _with_trading_client(
        self,
        fetch: Callable[[Any], dict[str, Any] | list[dict[str, Any]]],
        demo_factory: Callable[[], dict[str, Any] | list[dict[str, Any]]],
    ) -> dict[str, Any] | list[dict[str, Any]]:
        if self.settings.demo_mode:
            return demo_factory()
        if not self.settings.has_alpaca_credentials:
            raise AlpacaCredentialError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY to use Alpaca.")
        return fetch(self._get_trading_client())

    def _get_trading_client(self) -> Any:
        if not self.settings.has_alpaca_credentials:
            raise AlpacaCredentialError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY to use Alpaca.")
        if self._trading_client is None:
            from alpaca.trading.client import TradingClient

            self._trading_client = TradingClient(
                self.settings.alpaca_api_key,
                self.settings.alpaca_secret_key,
                paper=self.settings.alpaca_paper,
                url_override=_sdk_base_url(self.settings.alpaca_trading_base_url),
            )
        return self._trading_client

    def _get_stock_client(self) -> Any:
        if not self.settings.has_alpaca_credentials:
            raise AlpacaCredentialError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY to use Alpaca.")
        if self._stock_client is None:
            from alpaca.data.historical import StockHistoricalDataClient

            self._stock_client = StockHistoricalDataClient(
                self.settings.alpaca_api_key,
                self.settings.alpaca_secret_key,
                url_override=_sdk_base_url(self.settings.alpaca_data_base_url),
            )
        return self._stock_client

    def _get_option_client(self) -> Any:
        if not self.settings.has_alpaca_credentials:
            raise AlpacaCredentialError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY to use Alpaca.")
        if self._option_client is None:
            from alpaca.data.historical.option import OptionHistoricalDataClient

            self._option_client = OptionHistoricalDataClient(
                self.settings.alpaca_api_key,
                self.settings.alpaca_secret_key,
                url_override=_sdk_base_url(self.settings.alpaca_data_base_url),
            )
        return self._option_client


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    return dict(value)


def _build_order_request(payload: dict[str, Any]) -> Any:
    from alpaca.trading.enums import OrderClass, OrderSide, PositionIntent, TimeInForce
    from alpaca.trading.requests import LimitOrderRequest, OptionLegRequest

    client_order_id = payload.get("client_order_id")
    if payload.get("order_class") == "mleg":
        legs = [
            OptionLegRequest(
                symbol=leg["symbol"],
                side=OrderSide.BUY if leg["side"] == "buy" else OrderSide.SELL,
                ratio_qty=float(leg.get("ratio_qty", 1)),
                position_intent=_position_intent(leg["side"]),
            )
            for leg in payload["legs"]
        ]
        return LimitOrderRequest(
            qty=float(payload["qty"]),
            order_class=OrderClass.MLEG,
            time_in_force=TimeInForce.DAY,
            limit_price=float(payload["limit_price"]),
            legs=legs,
            client_order_id=client_order_id,
        )

    return LimitOrderRequest(
        symbol=payload["symbol"],
        qty=float(payload["qty"]),
        side=OrderSide.BUY if payload["side"] == "buy" else OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
        limit_price=float(payload["limit_price"]),
        client_order_id=client_order_id,
        position_intent=_position_intent(payload["side"]),
    )


def _position_intent(side: str) -> Any:
    from alpaca.trading.enums import PositionIntent

    return PositionIntent.BUY_TO_OPEN if side == "buy" else PositionIntent.SELL_TO_OPEN


def _option_expiration_window() -> tuple[str, str]:
    today = datetime.now(tz=UTC).date()
    start = today + timedelta(days=7)
    end = today + timedelta(days=30)
    return start.isoformat(), end.isoformat()


def _sdk_base_url(url: str) -> str:
    normalized = url.rstrip("/")
    if normalized.endswith("/v2"):
        return normalized.removesuffix("/v2")
    return normalized
