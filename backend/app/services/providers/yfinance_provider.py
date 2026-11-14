"""Provedor Yahoo Finance via biblioteca `yfinance`.

Não precisa de token e cobre B3 (sufixo `.SA`) e bolsas americanas (AAPL...).
É uma API não oficial: pode sofrer rate limit, por isso fica atrás do cache e
funciona como fallback da brapi (ou como provedor principal, se preferirem).
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timezone

from app.core.logging_config import log_event
from app.services.errors import ProviderUnavailableError, TickerNotFoundError
from app.services.providers.base import is_b3_ticker, iso_utc

logger = logging.getLogger(__name__)

# período do contrato -> período pedido ao Yahoo ("7d" é recortado depois)
_PERIOD_MAP = {"7d": "1mo", "1mo": "1mo", "6mo": "6mo", "1y": "1y"}


class YFinanceProvider:
    name = "yfinance"

    def supports(self, ticker: str) -> bool:
        return True

    @staticmethod
    def to_yahoo_symbol(ticker: str) -> str:
        """PETR4 -> PETR4.SA; AAPL, ^BVSP e PETR4.SA ficam como estão."""
        return f"{ticker}.SA" if is_b3_ticker(ticker) else ticker

    # ------------------------------------------------------------------ API
    def fetch_quote(self, ticker: str) -> dict:
        yf_ticker, rows = self._daily_rows(ticker, "5d")
        last = rows[-1]
        meta = self._metadata(yf_ticker)

        price = last["close"]
        if len(rows) >= 2:
            previous_close = rows[-2]["close"]
        else:
            previous_close = _number(meta.get("chartPreviousClose")) or price
        change = price - previous_close
        change_percent = change / previous_close * 100 if previous_close else 0.0

        market_time = meta.get("regularMarketTime")
        if isinstance(market_time, (int, float)):
            updated_at = datetime.fromtimestamp(market_time, timezone.utc)
        elif isinstance(market_time, datetime):
            updated_at = market_time
        else:
            updated_at = datetime.now(timezone.utc)

        return {
            "ticker": ticker,
            "name": meta.get("shortName") or meta.get("longName") or ticker,
            "currency": meta.get("currency") or ("BRL" if is_b3_ticker(ticker) else "USD"),
            "price": price,
            "change": change,
            "changePercent": change_percent,
            "previousClose": previous_close,
            "high": last["high"] or price,
            "low": last["low"] or price,
            "volume": int(last["volume"] or 0),
            "updatedAt": iso_utc(updated_at),
        }

    def fetch_history(self, ticker: str, period: str) -> list[dict]:
        _, rows = self._daily_rows(ticker, _PERIOD_MAP.get(period, period))
        return [{"date": row["date"], "close": row["close"]} for row in rows]

    # ------------------------------------------------------------- internos
    def _daily_rows(self, ticker: str, yahoo_period: str):
        symbol = self.to_yahoo_symbol(ticker)
        try:
            import yfinance as yf

            yf_ticker = yf.Ticker(symbol)
            frame = yf_ticker.history(period=yahoo_period, interval="1d", auto_adjust=False)
        except Exception as exc:  # rede, rate limit do Yahoo, mudança de layout...
            log_event(
                logger, logging.WARNING, "yfinance_unavailable",
                ticker=ticker, reason=f"{type(exc).__name__}: {exc}"[:200],
            )
            raise ProviderUnavailableError(
                f"Yahoo Finance indisponível ({type(exc).__name__})."
            ) from exc

        rows = []
        if frame is not None and not frame.empty:
            for index, row in frame.iterrows():
                close = _number(row.get("Close"))
                if close is None:  # pregão sem negócio / dado faltando
                    continue
                rows.append(
                    {
                        "date": index.date().isoformat(),
                        "close": close,
                        "high": _number(row.get("High")),
                        "low": _number(row.get("Low")),
                        "volume": _number(row.get("Volume")),
                    }
                )
        if not rows:
            # o yfinance devolve um DataFrame vazio para tickers inexistentes
            raise TickerNotFoundError(ticker)
        return yf_ticker, rows

    @staticmethod
    def _metadata(yf_ticker) -> dict:
        """Metadados do gráfico (nome, moeda, horário). Opcional: nunca falha."""
        try:
            return dict(yf_ticker.history_metadata or {})
        except Exception:
            return {}


def _number(value) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(number) else number
