"""Logging estruturado: cada linha é um evento com campos `chave=valor`.

Com `LOG_FORMAT=json` cada linha vira um objeto JSON (bom para ferramentas de
agregação de logs); com `LOG_FORMAT=text` fica legível no terminal.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.core.worker_config import get_settings

_FIELDS_ATTR = "quotly_fields"


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "quotly_event", record.getMessage()),
        }
        payload.update(getattr(record, _FIELDS_ATTR, {}))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging() -> None:
    """Configura o logging raiz. Chame uma vez na subida do processo."""
    settings = get_settings()
    handler = logging.StreamHandler()
    if settings.log_format == "json":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-7s %(name)s | %(message)s")
        )
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(settings.log_level)
    # bibliotecas barulhentas em nível INFO
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    *,
    exc_info: bool = False,
    **fields: Any,
) -> None:
    """Registra `event` com campos estruturados.

    Exemplo: `log_event(logger, logging.INFO, "alert_triggered", alert_id=7)`
    gera `alert_triggered alert_id=7` (texto) ou os mesmos campos em JSON.
    """
    text = " ".join([event, *(f"{k}={v}" for k, v in fields.items())])
    logger.log(
        level,
        text,
        exc_info=exc_info,
        extra={"quotly_event": event, _FIELDS_ATTR: fields},
    )
