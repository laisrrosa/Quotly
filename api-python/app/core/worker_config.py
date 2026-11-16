"""Configurações do módulo do Integrante 2 (cotações, e-mail e worker).

Tudo é lido de variáveis de ambiente (ou de um arquivo `.env` na raiz do
projeto). Veja `.env.example` para a lista completa.

Este arquivo é separado do config do back-end (Integrante 1) de propósito,
para os dois poderem evoluir sem conflito de merge.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# As variáveis deste módulo ficam em `backend/.env.worker` (e não no `.env` do
# back-end): a classe Settings do back-end rejeita variáveis que ela não
# conhece, então misturar os dois arquivos impediria a API de subir.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env.worker"

try:  # python-dotenv é opcional: sem ele, valem só as variáveis do ambiente
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE)
except ImportError:  # pragma: no cover
    pass


def _str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    return int(raw) if raw else default


def _float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    return float(raw) if raw else default


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on", "sim"}


@dataclass(frozen=True)
class WorkerSettings:
    # --- Cotações -----------------------------------------------------------
    market_providers: tuple[str, ...]  # ordem de tentativa (fallback)
    brapi_token: str
    brapi_base_url: str
    http_timeout_seconds: float
    quote_cache_ttl_seconds: int
    history_cache_ttl_seconds: int

    # --- E-mail -------------------------------------------------------------
    email_backend: str  # "smtp" ou "console" (só loga, para desenvolvimento)
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_use_tls: bool  # STARTTLS (porta 587)
    smtp_use_ssl: bool  # SSL direto (porta 465)
    email_from: str
    email_from_name: str
    app_url: str  # endereço do front-end, usado no link do e-mail
    display_timezone: str

    # --- Worker -------------------------------------------------------------
    alert_check_interval_minutes: int
    alert_model_path: str
    user_model_path: str
    stock_model_path: str
    db_session_factory_path: str

    # --- Logs ---------------------------------------------------------------
    log_level: str
    log_format: str  # "text" ou "json"


@lru_cache
def get_settings() -> WorkerSettings:
    providers = tuple(
        p.strip().lower()
        for p in _str("MARKET_PROVIDERS", "brapi,yfinance").split(",")
        if p.strip()
    )
    return WorkerSettings(
        market_providers=providers,
        brapi_token=_str("BRAPI_TOKEN"),
        brapi_base_url=_str("BRAPI_BASE_URL", "https://brapi.dev"),
        http_timeout_seconds=_float("MARKET_HTTP_TIMEOUT", 10.0),
        quote_cache_ttl_seconds=_int("QUOTE_CACHE_TTL", 60),
        history_cache_ttl_seconds=_int("HISTORY_CACHE_TTL", 900),
        email_backend=_str("EMAIL_BACKEND", "console").lower(),
        smtp_host=_str("SMTP_HOST"),
        smtp_port=_int("SMTP_PORT", 587),
        smtp_user=_str("SMTP_USER"),
        smtp_password=_str("SMTP_PASSWORD"),
        smtp_use_tls=_bool("SMTP_USE_TLS", True),
        smtp_use_ssl=_bool("SMTP_USE_SSL", False),
        email_from=_str("EMAIL_FROM", "alertas@quotly.local"),
        email_from_name=_str("EMAIL_FROM_NAME", "Quotly"),
        app_url=_str("APP_URL", "http://localhost:5173").rstrip("/"),
        display_timezone=_str("DISPLAY_TIMEZONE", "America/Sao_Paulo"),
        alert_check_interval_minutes=_int("ALERT_CHECK_INTERVAL_MINUTES", 5),
        alert_model_path=_str("ALERT_MODEL_PATH", "app.models:Alert"),
        user_model_path=_str("USER_MODEL_PATH", "app.models:User"),
        stock_model_path=_str("STOCK_MODEL_PATH", "app.models:StockQuote"),
        db_session_factory_path=_str(
            "DB_SESSION_FACTORY_PATH", "app.database.session:SessionLocal"
        ),
        log_level=_str("LOG_LEVEL", "INFO").upper(),
        log_format=_str("LOG_FORMAT", "text").lower(),
    )
