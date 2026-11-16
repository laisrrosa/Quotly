"""Ponte entre o monitor de alertas e os modelos SQLAlchemy do Integrante 1.

O repositório recebe as classes `Alert` e `User` e a fábrica de sessões por
parâmetro, então não importa em que arquivo o back-end as definiu. Ele aceita
os dois formatos de tabela que aparecem na documentação do grupo:

- API_CONTRACT.md: coluna `status` ("active" | "triggered" | "disabled")
  e `triggered_at`;
- workflow do Integrante 1: colunas booleanas `is_triggered` e `is_active`.

O valor de `condition` pode estar como "above"/"below" ou "ABOVE"/"BELOW".
"""
from __future__ import annotations

import importlib
from datetime import datetime
from typing import Any, Callable

from sqlalchemy import select, update

from app.core.worker_config import get_settings
from app.workers.alert_monitor import ABOVE, BELOW, PendingAlert

STATUS_ACTIVE = "active"
STATUS_TRIGGERED = "triggered"

_CONDITION_ALIASES = {
    "above": ABOVE, "acima": ABOVE, "gt": ABOVE, "gte": ABOVE,
    "below": BELOW, "abaixo": BELOW, "lt": BELOW, "lte": BELOW,
}


def normalize_condition(raw: Any) -> str:
    value = getattr(raw, "value", raw)  # aceita Enum
    try:
        return _CONDITION_ALIASES[str(value).strip().lower()]
    except KeyError:
        raise ValueError(f'Condição de alerta desconhecida: "{raw}"') from None


class SqlAlchemyAlertRepository:
    def __init__(
        self,
        session_factory: Callable[[], Any],
        alert_model: Any,
        user_model: Any,
        stock_model: Any | None = None,
    ):
        self._session_factory = session_factory
        self._Alert = alert_model
        self._User = user_model
        self._Stock = stock_model
        self._uses_status = hasattr(alert_model, "status")
        if not self._uses_status and not hasattr(alert_model, "is_triggered"):
            raise TypeError(
                "O modelo Alert precisa ter a coluna `status` ou a coluna `is_triggered`."
            )
        self._has_triggered_at = hasattr(alert_model, "triggered_at")
        self._has_is_active = hasattr(alert_model, "is_active")

    # ----------------------------------------------------------- consultas
    def list_pending(self) -> list[PendingAlert]:
        Alert, User = self._Alert, self._User
        query = (
            select(Alert, User)
            .join(User, User.id == Alert.user_id)
            .where(*self._pending_filter())
            .order_by(Alert.id)
        )
        with self._session_factory() as session:
            rows = session.execute(query).all()
            return [
                PendingAlert(
                    id=alert.id,
                    ticker=str(alert.ticker).strip().upper(),
                    target_price=float(alert.target_price),
                    condition=normalize_condition(alert.condition),
                    user_email=user.email,
                    user_name=getattr(user, "name", "") or "",
                )
                for alert, user in rows
            ]

    # ---------------------------------------------------------- alterações
    def mark_triggered(self, alert_id: int, triggered_at: datetime) -> bool:
        values: dict[str, Any] = (
            {"status": STATUS_TRIGGERED} if self._uses_status else {"is_triggered": True}
        )
        if self._has_triggered_at:
            values["triggered_at"] = triggered_at
        # UPDATE condicional: só altera se o alerta ainda está pendente
        statement = (
            update(self._Alert)
            .where(self._Alert.id == alert_id, *self._pending_filter())
            .values(**values)
        )
        with self._session_factory() as session:
            changed = session.execute(statement).rowcount
            session.commit()
        return changed == 1

    def release(self, alert_id: int) -> None:
        values: dict[str, Any] = (
            {"status": STATUS_ACTIVE} if self._uses_status else {"is_triggered": False}
        )
        if self._has_triggered_at:
            values["triggered_at"] = None
        statement = update(self._Alert).where(self._Alert.id == alert_id).values(**values)
        with self._session_factory() as session:
            session.execute(statement)
            session.commit()

    def save_quote(self, quote: dict) -> None:
        """Grava a cotação em `stock_quotes` (alimenta /api/stocks/{ticker})."""
        if self._Stock is None:
            return
        with self._session_factory() as session:
            session.add(
                self._Stock(
                    ticker=quote["ticker"],
                    price=quote["price"],
                    high_price=quote.get("high"),
                    low_price=quote.get("low"),
                    change_percent=quote.get("changePercent"),
                )
            )
            session.commit()

    # ------------------------------------------------------------- internos
    def _pending_filter(self) -> list:
        Alert = self._Alert
        if self._uses_status:
            return [Alert.status == STATUS_ACTIVE]
        conditions = [Alert.is_triggered.is_(False)]
        if self._has_is_active:
            conditions.append(Alert.is_active.is_(True))
        return conditions


def _load(path: str) -> Any:
    """Importa `pacote.modulo:Nome`."""
    module_name, _, attribute = path.partition(":")
    try:
        return getattr(importlib.import_module(module_name), attribute)
    except (ImportError, AttributeError) as exc:
        raise RuntimeError(
            f'Não foi possível importar "{path}". Ajuste ALERT_MODEL_PATH, USER_MODEL_PATH '
            "e DB_SESSION_FACTORY_PATH no .env para apontar para o código do back-end."
        ) from exc


def build_default_repository() -> SqlAlchemyAlertRepository:
    """Monta o repositório com os modelos/sessão indicados no `.env.worker`."""
    settings = get_settings()
    try:
        stock_model = _load(settings.stock_model_path) if settings.stock_model_path else None
    except RuntimeError:  # back-end sem tabela de cotações: só não grava snapshots
        stock_model = None
    return SqlAlchemyAlertRepository(
        session_factory=_load(settings.db_session_factory_path),
        alert_model=_load(settings.alert_model_path),
        user_model=_load(settings.user_model_path),
        stock_model=stock_model,
    )
