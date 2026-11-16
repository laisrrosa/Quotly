"""Provedor brapi.dev (ações da B3), usando a API v2.

- Cotação:   GET /api/v2/stocks/quote?symbols=PETR4
- Histórico: GET /api/v2/stocks/historical?symbols=PETR4&range=1mo&interval=1d

Sem token só funcionam as ações de teste (PETR4, VALE3, MGLU3, ITUB4). Com o
token do plano gratuito funcionam todas, mas o histórico é limitado; quando a
brapi recusa um pedido por causa do plano, levantamos ProviderUnavailableError
e o `market_data` tenta o próximo provedor (yfinance).
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import httpx

from app.core.logging_config import log_event
from app.services.errors import ProviderUnavailableError, TickerNotFoundError
from app.services.providers.base import is_b3_ticker, iso_utc

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class BrapiProvider:
    name = "brapi"

    def __init__(
        self,
        token: str = "",
        base_url: str = "https://brapi.dev",
        timeout: float = 10.0,
        max_retries: int = 2,
        backoff_seconds: float = 0.5,
        client: httpx.Client | None = None,
    ):
        self._token = token
        self._max_retries = max_retries
        self._backoff = backoff_seconds
        self._client = client or httpx.Client(base_url=base_url, timeout=timeout)

    def supports(self, ticker: str) -> bool:
        return is_b3_ticker(ticker) or ticker == "^BVSP"

    # ------------------------------------------------------------------ API
    def fetch_quote(self, ticker: str) -> dict:
        data = self._first_result("/api/v2/stocks/quote", {"symbols": ticker}, ticker)
        price = data.get("regularMarketPrice")
        if price is None:
            raise TickerNotFoundError(ticker)

        previous_close = data.get("regularMarketPreviousClose")
        change = data.get("regularMarketChange")
        change_percent = data.get("regularMarketChangePercent")
        if previous_close is None and change is not None:
            previous_close = price - change
        if change is None and previous_close is not None:
            change = price - previous_close
        if change_percent is None and previous_close:
            change_percent = (change or 0.0) / previous_close * 100

        return {
            "ticker": ticker,
            "name": data.get("shortName") or data.get("longName") or ticker,
            "currency": data.get("currency") or "BRL",
            "price": float(price),
            "change": float(change or 0.0),
            "changePercent": float(change_percent or 0.0),
            "previousClose": float(previous_close if previous_close is not None else price),
            "high": float(data.get("regularMarketDayHigh") or price),
            "low": float(data.get("regularMarketDayLow") or price),
            "volume": int(data.get("regularMarketVolume") or 0),
            "updatedAt": _parse_time(data.get("regularMarketTime")),
        }

    def fetch_history(self, ticker: str, period: str) -> list[dict]:
        data = self._first_result(
            "/api/v2/stocks/historical",
            {"symbols": ticker, "range": period, "interval": "1d", "sortOrder": "asc"},
            ticker,
        )
        points = []
        for item in data.get("historicalDataPrice") or []:
            if item.get("close") is None or item.get("date") is None:
                continue
            day = datetime.fromtimestamp(int(item["date"]), timezone.utc).date()
            points.append({"date": day.isoformat(), "close": float(item["close"])})
        if not points:
            raise TickerNotFoundError(ticker)
        return points

    # ------------------------------------------------------------- internos
    def _first_result(self, path: str, params: dict, ticker: str) -> dict:
        payload = self._get(path, params, ticker)
        results = payload.get("results") or []
        if not results:
            raise TickerNotFoundError(ticker)
        first = results[0]
        # v2 aninha os campos em "data"; aceitamos também o formato plano (v1)
        return first.get("data") or first

    def _get(self, path: str, params: dict, ticker: str) -> dict:
        headers = {"Authorization": f"Bearer {self._token}"} if self._token else {}
        last_problem = "sem resposta"

        for attempt in range(self._max_retries + 1):
            if attempt:
                time.sleep(self._backoff * 2 ** (attempt - 1))
            try:
                response = self._client.get(path, params=params, headers=headers)
            except httpx.HTTPError as exc:  # timeout, DNS, conexão recusada...
                last_problem = f"erro de rede ({type(exc).__name__})"
                continue

            status = response.status_code
            if status == 200:
                try:
                    return response.json()
                except ValueError:
                    last_problem = "resposta não é JSON"
                    continue
            if status == 404:
                raise TickerNotFoundError(ticker)
            if status in _RETRYABLE_STATUS:
                last_problem = "rate limit (429)" if status == 429 else f"HTTP {status}"
                continue
            # 400 (fora do limite do plano), 401/403 (token ausente/sem permissão):
            # repetir não adianta, mas outro provedor pode atender.
            log_event(
                logger, logging.WARNING, "brapi_request_refused",
                ticker=ticker, status=status, path=path,
            )
            raise ProviderUnavailableError(f"brapi recusou a requisição (HTTP {status}).")

        log_event(
            logger, logging.WARNING, "brapi_unavailable",
            ticker=ticker, path=path, reason=last_problem,
        )
        raise ProviderUnavailableError(f"brapi indisponível: {last_problem}.")


def _parse_time(raw: object) -> str:
    """Aceita ISO 8601 (v2) ou timestamp Unix; na dúvida, usa o horário atual."""
    try:
        if isinstance(raw, (int, float)):
            return iso_utc(datetime.fromtimestamp(raw, timezone.utc))
        if isinstance(raw, str) and raw:
            return iso_utc(datetime.fromisoformat(raw.replace("Z", "+00:00")))
    except (ValueError, OSError, OverflowError):
        pass
    return iso_utc(datetime.now(timezone.utc))
