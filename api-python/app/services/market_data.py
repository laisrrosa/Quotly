"""Serviço de cotações do Quotly (Integrante 2).

Funções públicas, já no formato do `API_CONTRACT.md`:

    get_current_quote("PETR4")            -> dict  (GET /api/quotes/{ticker})
    get_historical_quotes("PETR4", "1mo") -> list  (GET /api/quotes/{ticker}/history)
    get_current_quotes(["PETR4", "AAPL"]) -> dict  (usada pelo worker de alertas)

Por baixo:
- vários provedores em ordem de preferência (`MARKET_PROVIDERS`), com fallback
  automático quando um falha ou não conhece o ticker;
- cache em memória com TTL, que reduz chamadas externas (rate limit) e serve o
  último valor conhecido se todos os provedores estiverem fora do ar.

As funções são síncronas. No FastAPI, use-as em rotas `def` (não `async def`)
para que rodem no threadpool e não travem o event loop.
"""
from __future__ import annotations

import logging
import re
import threading
import time
from datetime import date, timedelta
from typing import Callable, Iterable

from app.core.logging_config import log_event
from app.core.worker_config import get_settings
from app.services.errors import (
    InvalidRangeError,
    MarketDataError,
    ProviderUnavailableError,
    TickerNotFoundError,
)
from app.services.providers import BrapiProvider, MarketDataProvider, YFinanceProvider

logger = logging.getLogger(__name__)

VALID_RANGES: tuple[str, ...] = ("7d", "1mo", "6mo", "1y")
_TICKER_PATTERN = re.compile(r"^[A-Z0-9^][A-Z0-9.\-=]{0,14}$")


def normalize_ticker(ticker: str) -> str:
    """` petr4 ` -> `PETR4`. Levanta TickerNotFoundError se o formato é inválido."""
    cleaned = (ticker or "").strip().upper()
    if not _TICKER_PATTERN.match(cleaned):
        raise TickerNotFoundError(cleaned or str(ticker))
    return cleaned


class _TTLCache:
    """Cache em memória, seguro para threads (API + worker no mesmo processo)."""

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._lock = threading.Lock()
        self._items: dict[tuple, tuple[float, object]] = {}

    def get(self, key: tuple, ttl: float) -> tuple[object | None, bool]:
        """Devolve `(valor, ainda_válido)`; `(None, False)` se nunca foi salvo."""
        with self._lock:
            entry = self._items.get(key)
        if entry is None:
            return None, False
        saved_at, value = entry
        return value, (self._clock() - saved_at) < ttl

    def set(self, key: tuple, value: object) -> None:
        with self._lock:
            self._items[key] = (self._clock(), value)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


class MarketDataService:
    def __init__(
        self,
        providers: Iterable[MarketDataProvider],
        quote_ttl: float = 60,
        history_ttl: float = 900,
        clock: Callable[[], float] = time.monotonic,
        today: Callable[[], date] = date.today,
    ):
        self._providers = list(providers)
        if not self._providers:
            raise ValueError("Configure ao menos um provedor de cotações.")
        self._quote_ttl = quote_ttl
        self._history_ttl = history_ttl
        self._cache = _TTLCache(clock)
        self._today = today

    # ------------------------------------------------------------------ API
    def get_current_quote(self, ticker: str) -> dict:
        symbol = normalize_ticker(ticker)
        quote = self._cached(
            ("quote", symbol),
            self._quote_ttl,
            lambda: _round_quote(
                self._from_providers(symbol, lambda p: p.fetch_quote(symbol))
            ),
            symbol,
        )
        return dict(quote)

    def get_historical_quotes(self, ticker: str, period: str = "1mo") -> list[dict]:
        if period not in VALID_RANGES:
            raise InvalidRangeError(period, VALID_RANGES)
        symbol = normalize_ticker(ticker)
        history = self._cached(
            ("history", symbol, period),
            self._history_ttl,
            lambda: self._clean_history(
                self._from_providers(symbol, lambda p: p.fetch_history(symbol, period)),
                period,
                symbol,
            ),
            symbol,
        )
        return [dict(point) for point in history]

    def get_current_quotes(self, tickers: Iterable[str]) -> dict[str, dict]:
        """Cotações de vários tickers (sem repetir chamadas para duplicados).

        Tickers que falharem ficam de fora do resultado: quem chama (o worker)
        simplesmente tenta de novo no próximo ciclo.
        """
        quotes: dict[str, dict] = {}
        for raw in dict.fromkeys(tickers):  # remove duplicados mantendo a ordem
            try:
                quote = self.get_current_quote(raw)
            except MarketDataError as exc:
                log_event(
                    logger, logging.WARNING, "quote_fetch_failed",
                    ticker=raw, reason=str(exc),
                )
                continue
            quotes[quote["ticker"]] = quote
        return quotes

    def clear_cache(self) -> None:
        self._cache.clear()

    # ------------------------------------------------------------- internos
    def _cached(self, key: tuple, ttl: float, load: Callable[[], object], symbol: str):
        value, fresh = self._cache.get(key, ttl)
        if fresh:
            return value
        try:
            loaded = load()
        except ProviderUnavailableError:
            if value is not None:  # melhor um dado um pouco antigo do que um erro
                log_event(logger, logging.WARNING, "serving_stale_cache", ticker=symbol, kind=key[0])
                return value
            raise
        self._cache.set(key, loaded)
        return loaded

    def _from_providers(self, symbol: str, call: Callable[[MarketDataProvider], object]):
        candidates = [p for p in self._providers if p.supports(symbol)]
        any_unavailable = False
        for provider in candidates:
            try:
                result = call(provider)
            except TickerNotFoundError:
                continue  # outro provedor pode conhecer (ex.: AAPL não está na brapi)
            except ProviderUnavailableError:
                any_unavailable = True
                continue
            except Exception:  # bug/mudança inesperada no provedor: não derruba a API
                log_event(
                    logger, logging.ERROR, "provider_unexpected_error",
                    exc_info=True, provider=provider.name, ticker=symbol,
                )
                any_unavailable = True
                continue
            log_event(logger, logging.DEBUG, "provider_ok", provider=provider.name, ticker=symbol)
            return result

        if any_unavailable:
            raise ProviderUnavailableError()
        raise TickerNotFoundError(symbol)

    def _clean_history(self, points: list[dict], period: str, symbol: str) -> list[dict]:
        """Ordena por data, remove duplicados, arredonda e recorta o período `7d`."""
        by_date = {p["date"]: round(float(p["close"]), 2) for p in points}
        if period == "7d":
            cutoff = (self._today() - timedelta(days=7)).isoformat()
            by_date = {d: c for d, c in by_date.items() if d >= cutoff} or dict(
                sorted(by_date.items())[-5:]  # feriadão: devolve os 5 últimos pregões
            )
        if not by_date:
            raise TickerNotFoundError(symbol)
        return [{"date": d, "close": c} for d, c in sorted(by_date.items())]


def _round_quote(quote: dict) -> dict:
    for field in ("price", "change", "changePercent", "previousClose", "high", "low"):
        quote[field] = round(float(quote[field]), 2)
    return quote


# ---------------------------------------------------------------- serviço padrão
_PROVIDER_FACTORIES: dict[str, Callable[[], MarketDataProvider]] = {
    "brapi": lambda: BrapiProvider(
        token=get_settings().brapi_token,
        base_url=get_settings().brapi_base_url,
        timeout=get_settings().http_timeout_seconds,
    ),
    "yfinance": lambda: YFinanceProvider(),
}

_default_service: MarketDataService | None = None
_default_lock = threading.Lock()


def get_market_data_service() -> MarketDataService:
    """Instância única (com cache compartilhado) montada a partir do `.env`."""
    global _default_service
    with _default_lock:
        if _default_service is None:
            settings = get_settings()
            unknown = [n for n in settings.market_providers if n not in _PROVIDER_FACTORIES]
            if unknown:
                raise ValueError(
                    f"MARKET_PROVIDERS inválido: {unknown}. Opções: {sorted(_PROVIDER_FACTORIES)}"
                )
            _default_service = MarketDataService(
                [_PROVIDER_FACTORIES[name]() for name in settings.market_providers],
                quote_ttl=settings.quote_cache_ttl_seconds,
                history_ttl=settings.history_cache_ttl_seconds,
            )
        return _default_service


def get_current_quote(ticker: str) -> dict:
    """Cotação atual: preço, variação, máxima/mínima, volume e data/hora."""
    return get_market_data_service().get_current_quote(ticker)


def get_historical_quotes(ticker: str, period: str = "1mo") -> list[dict]:
    """Fechamentos diários em ordem cronológica. `period`: 7d | 1mo | 6mo | 1y."""
    return get_market_data_service().get_historical_quotes(ticker, period)


def get_current_quotes(tickers: Iterable[str]) -> dict[str, dict]:
    """Cotações de vários tickers de uma vez; os que falharem ficam de fora."""
    return get_market_data_service().get_current_quotes(tickers)
