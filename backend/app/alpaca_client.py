from collections.abc import Callable
from typing import Any

from app.config import Settings
from app.demo_data import (
    demo_account,
    demo_clock,
    demo_option_chain,
    demo_option_contracts,
    demo_orders,
    demo_positions,
    demo_stock_snapshots,
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

    def option_contracts(self, symbol: str) -> dict[str, Any]:
        if self.settings.demo_mode:
            return demo_option_contracts(symbol)
        if not self.settings.has_alpaca_credentials:
            raise AlpacaCredentialError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY to use Alpaca.")

        from alpaca.trading.requests import GetOptionContractsRequest

        client = self._get_trading_client()
        contracts = client.get_option_contracts(GetOptionContractsRequest(underlying_symbols=[symbol]))
        return _model_dump(contracts)

    def option_chain(self, symbol: str) -> dict[str, Any]:
        if self.settings.demo_mode:
            return demo_option_chain(symbol)
        if not self.settings.has_alpaca_credentials:
            raise AlpacaCredentialError("Set ALPACA_API_KEY and ALPACA_SECRET_KEY to use Alpaca.")

        from alpaca.data.requests import OptionChainRequest

        client = self._get_option_client()
        chain = client.get_option_chain(OptionChainRequest(underlying_symbol=symbol))
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
            )
        return self._option_client


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    return dict(value)
