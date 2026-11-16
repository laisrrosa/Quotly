"""Monitor de alertas de preço (Integrante 2).

A cada ciclo (`AlertMonitor.run_cycle`):

1. busca no banco os alertas ativos e ainda não disparados;
2. junta os tickers únicos, para consultar cada ativo uma única vez;
3. obtém os preços atuais;
4. para cada alerta, verifica a condição:
     "above" -> preço atual >= preço-alvo
     "below" -> preço atual <= preço-alvo
5. se atingiu: marca o alerta como disparado no banco e envia o e-mail.

Sobre o passo 5: o alerta é marcado como disparado **antes** do envio, com um
UPDATE condicional (só vale se ele ainda estiver ativo). Assim, mesmo que dois
workers rodem ao mesmo tempo (ex.: `uvicorn --workers 2`), só um deles envia o
e-mail. Se o envio falhar, o alerta volta a ficar ativo e é tentado de novo no
ciclo seguinte.

O monitor não conhece SQLAlchemy nem SMTP: recebe um repositório, uma função
de cotações e uma função de e-mail. Isso deixa a lógica fácil de testar.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Iterable, Protocol

from app.core.logging_config import log_event

logger = logging.getLogger(__name__)

ABOVE = "above"
BELOW = "below"


@dataclass(frozen=True)
class PendingAlert:
    """O que o monitor precisa saber de um alerta ativo."""

    id: int
    ticker: str
    target_price: float
    condition: str  # "above" | "below"
    user_email: str
    user_name: str = ""


class AlertRepository(Protocol):
    """Acesso ao banco. Implementação real: `SqlAlchemyAlertRepository`."""

    def list_pending(self) -> list[PendingAlert]:
        """Alertas ativos e não disparados, com o e-mail do dono."""

    def mark_triggered(self, alert_id: int, triggered_at: datetime) -> bool:
        """Marca como disparado. `False` se o alerta já não estava ativo."""

    def release(self, alert_id: int) -> None:
        """Desfaz `mark_triggered` (usado quando o e-mail falha)."""

    # Opcional: se o repositório tiver `save_quote(quote: dict)`, o monitor grava
    # um registro de cada cotação consultada (tabela `stock_quotes`), que é o
    # que alimenta os endpoints /api/stocks do back-end.


@dataclass
class CycleResult:
    """Resumo de um ciclo, usado nos logs e nos testes."""

    checked: int = 0
    triggered: int = 0
    email_failures: int = 0
    tickers: int = 0
    tickers_without_quote: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    error: str | None = None


def is_condition_met(condition: str, current_price: float, target_price: float) -> bool:
    if condition == ABOVE:
        return current_price >= target_price
    if condition == BELOW:
        return current_price <= target_price
    raise ValueError(f'Condição desconhecida: "{condition}"')


class AlertMonitor:
    def __init__(
        self,
        repository: AlertRepository,
        fetch_quotes: Callable[[Iterable[str]], dict[str, dict]] | None = None,
        send_email: Callable[..., None] | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        if fetch_quotes is None:
            from app.services.market_data import get_current_quotes as fetch_quotes
        if send_email is None:
            from app.services.email_service import send_alert_email as send_email
        self._repository = repository
        self._fetch_quotes = fetch_quotes
        self._send_email = send_email
        self._now = now

    def run_cycle(self) -> CycleResult:
        """Executa um ciclo completo. Nunca levanta exceção: falhas vão para o log."""
        started = time.monotonic()
        result = CycleResult()
        try:
            self._run(result)
        except Exception as exc:  # banco fora do ar, bug inesperado...
            result.error = f"{type(exc).__name__}: {exc}"
            log_event(logger, logging.ERROR, "alert_cycle_failed", exc_info=True, error=result.error)
        result.duration_seconds = round(time.monotonic() - started, 3)
        log_event(
            logger, logging.INFO, "alert_cycle_finished",
            checked=result.checked,
            triggered=result.triggered,
            email_failures=result.email_failures,
            tickers=result.tickers,
            tickers_without_quote=",".join(result.tickers_without_quote) or "-",
            duration_s=result.duration_seconds,
        )
        return result

    # ------------------------------------------------------------- internos
    def _run(self, result: CycleResult) -> None:
        alerts = self._repository.list_pending()
        if not alerts:
            return

        tickers = sorted({alert.ticker.strip().upper() for alert in alerts})
        result.tickers = len(tickers)
        quotes = self._fetch_quotes(tickers)
        result.tickers_without_quote = [t for t in tickers if t not in quotes]
        self._save_snapshots(quotes.values())

        for alert in alerts:
            quote = quotes.get(alert.ticker.strip().upper())
            if quote is None:
                continue  # sem cotação agora: tenta de novo no próximo ciclo
            result.checked += 1
            try:
                self._check(alert, quote, result)
            except Exception as exc:  # um alerta com problema não para os demais
                log_event(
                    logger, logging.ERROR, "alert_check_failed",
                    exc_info=True, alert_id=alert.id, error=f"{type(exc).__name__}: {exc}",
                )

    def _save_snapshots(self, quotes: Iterable[dict]) -> None:
        save = getattr(self._repository, "save_quote", None)
        if save is None:
            return
        for quote in quotes:
            try:
                save(quote)
            except Exception as exc:  # um snapshot que falha não pode impedir o alerta
                log_event(
                    logger, logging.WARNING, "quote_snapshot_failed",
                    ticker=quote.get("ticker"), error=f"{type(exc).__name__}: {exc}",
                )

    def _check(self, alert: PendingAlert, quote: dict, result: CycleResult) -> None:
        current_price = float(quote["price"])
        if not is_condition_met(alert.condition, current_price, alert.target_price):
            return

        triggered_at = self._now()
        if not self._repository.mark_triggered(alert.id, triggered_at):
            return  # outro worker já cuidou deste alerta

        try:
            self._send_email(
                to_email=alert.user_email,
                user_name=alert.user_name,
                ticker=alert.ticker,
                condition=alert.condition,
                target_price=alert.target_price,
                current_price=current_price,
                currency=quote.get("currency", "BRL"),
                triggered_at=triggered_at,
            )
        except Exception as exc:
            self._repository.release(alert.id)
            result.email_failures += 1
            log_event(
                logger, logging.ERROR, "alert_email_failed",
                alert_id=alert.id, ticker=alert.ticker, error=f"{type(exc).__name__}: {exc}",
            )
            return

        result.triggered += 1
        log_event(
            logger, logging.INFO, "alert_triggered",
            alert_id=alert.id, ticker=alert.ticker, condition=alert.condition,
            target_price=alert.target_price, current_price=current_price,
        )
