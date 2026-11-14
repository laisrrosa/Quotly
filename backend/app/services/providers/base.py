"""Interface comum dos provedores de cotação.

Cada provedor devolve os dados **já no formato do API_CONTRACT.md**, de modo
que o resto do sistema não precisa saber de onde a cotação veio.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Protocol

# PETR4, VALE3, BOVA11, TAEE11, PETR4F (fracionário)...
_B3_PATTERN = re.compile(r"^[A-Z]{4}\d{1,2}F?$")


def is_b3_ticker(ticker: str) -> bool:
    return bool(_B3_PATTERN.match(ticker))


def iso_utc(moment: datetime) -> str:
    """`2026-10-24T18:30:00Z` (formato de data/hora do contrato)."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class MarketDataProvider(Protocol):
    name: str

    def supports(self, ticker: str) -> bool:
        """Se vale a pena perguntar a este provedor sobre o ticker."""

    def fetch_quote(self, ticker: str) -> dict:
        """Cotação atual. Levanta TickerNotFoundError / ProviderUnavailableError."""

    def fetch_history(self, ticker: str, period: str) -> list[dict]:
        """Fechamentos diários `[{"date": "YYYY-MM-DD", "close": float}]`."""
