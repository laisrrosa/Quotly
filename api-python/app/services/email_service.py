"""Envio de e-mails de alerta do Quotly (Integrante 2).

Uso principal (é o que o worker chama):

    send_alert_email(
        to_email="maria@email.com", user_name="Maria", ticker="PETR4",
        condition="above", target_price=38.0, current_price=38.5,
    )

Backends (`EMAIL_BACKEND` no `.env`):
- `console`: não envia nada, só registra o e-mail no log (padrão, para dev);
- `smtp`: envia de verdade via SMTP (Gmail com senha de app, Brevo, Mailtrap...).
"""
from __future__ import annotations

import html
import logging
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path
from string import Template

from app.core.logging_config import log_event
from app.core.worker_config import WorkerSettings, get_settings
from app.services.errors import EmailSendError

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"
_CURRENCY_SYMBOLS = {"BRL": "R$", "USD": "US$", "EUR": "€"}

# condição -> (frase, rótulo, seta, cor do destaque, fundo do destaque)
_CONDITION_STYLE = {
    "above": ("subiu acima de", "Subir acima de", "▲", "#15803d", "#f0fdf4"),
    "below": ("caiu abaixo de", "Cair abaixo de", "▼", "#b91c1c", "#fef2f2"),
}


def format_price(value: float, currency: str = "BRL") -> str:
    """38.5 -> `R$ 38,50`; 1234.5 em USD -> `US$ 1.234,50` (padrão brasileiro)."""
    number = f"{value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    symbol = _CURRENCY_SYMBOLS.get((currency or "BRL").upper(), (currency or "").upper())
    return f"{symbol} {number}".strip()


def _local_time(moment: datetime, tz_name: str) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    try:
        from zoneinfo import ZoneInfo

        local = moment.astimezone(ZoneInfo(tz_name))
    except Exception:  # sem base de fusos (Windows sem `tzdata`): usa UTC-3
        local = moment.astimezone(timezone(timedelta(hours=-3)))
    return local.strftime("%d/%m/%Y às %H:%M")


def build_alert_email(
    *,
    to_email: str,
    user_name: str,
    ticker: str,
    condition: str,
    target_price: float,
    current_price: float,
    currency: str = "BRL",
    triggered_at: datetime | None = None,
    settings: WorkerSettings | None = None,
) -> EmailMessage:
    """Monta a mensagem (texto puro + HTML) sem enviar. Útil para testes."""
    settings = settings or get_settings()
    condition = condition.lower()
    if condition not in _CONDITION_STYLE:
        raise ValueError(f'Condição inválida: "{condition}". Use "above" ou "below".')
    text, label, arrow, color, background = _CONDITION_STYLE[condition]

    values = {
        "user_name": (user_name or "").strip() or "investidor(a)",
        "ticker": ticker.upper(),
        "condition_text": text,
        "condition_label": label,
        "target_price": format_price(target_price, currency),
        "current_price": format_price(current_price, currency),
        "triggered_at": _local_time(
            triggered_at or datetime.now(timezone.utc), settings.display_timezone
        ),
        "alerts_url": f"{settings.app_url}/alerts",
        "arrow": arrow,
        "accent_color": color,
        "accent_bg": background,
    }
    # No HTML, tudo que vem do usuário/banco é escapado (evita injeção de HTML).
    html_values = {key: html.escape(str(value)) for key, value in values.items()}

    message = EmailMessage()
    message["Subject"] = (
        f"[Quotly] Alerta de Preço: {values['ticker']} atingiu {values['current_price']}"
    )
    message["From"] = formataddr((settings.email_from_name, settings.email_from))
    message["To"] = to_email
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain="quotly.local")
    message.set_content(_render("alert.txt", values))
    message.add_alternative(_render("alert.html", html_values), subtype="html")
    return message


def send_email(message: EmailMessage, settings: WorkerSettings | None = None) -> None:
    """Envia uma mensagem pronta. Levanta EmailSendError em caso de falha."""
    settings = settings or get_settings()
    recipient = message["To"]

    if settings.email_backend == "console":
        body = message.get_body(preferencelist=("plain",))
        log_event(
            logger, logging.INFO, "email_console",
            to=recipient, subject=message["Subject"],
        )
        logger.info("Conteúdo do e-mail (não enviado):\n%s", body.get_content() if body else "")
        return

    if settings.email_backend != "smtp":
        raise EmailSendError(f'EMAIL_BACKEND inválido: "{settings.email_backend}".')
    if not settings.smtp_host:
        raise EmailSendError("SMTP_HOST não configurado. Veja o arquivo .env.example.")

    try:
        context = ssl.create_default_context()
        timeout = settings.http_timeout_seconds
        if settings.smtp_use_ssl:
            server = smtplib.SMTP_SSL(
                settings.smtp_host, settings.smtp_port, timeout=timeout, context=context
            )
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=timeout)
        with server:
            if settings.smtp_use_tls and not settings.smtp_use_ssl:
                server.starttls(context=context)
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
    except (smtplib.SMTPException, OSError) as exc:
        log_event(
            logger, logging.ERROR, "email_failed",
            to=recipient, reason=f"{type(exc).__name__}: {exc}"[:200],
        )
        raise EmailSendError(f"Falha ao enviar e-mail para {recipient}: {exc}") from exc

    log_event(logger, logging.INFO, "email_sent", to=recipient, subject=message["Subject"])


def send_alert_email(
    *,
    to_email: str,
    user_name: str,
    ticker: str,
    condition: str,
    target_price: float,
    current_price: float,
    currency: str = "BRL",
    triggered_at: datetime | None = None,
) -> None:
    """Monta e envia o e-mail de alerta atingido."""
    message = build_alert_email(
        to_email=to_email,
        user_name=user_name,
        ticker=ticker,
        condition=condition,
        target_price=target_price,
        current_price=current_price,
        currency=currency,
        triggered_at=triggered_at,
    )
    send_email(message)


def _render(template_name: str, values: dict) -> str:
    template = Template((_TEMPLATES_DIR / template_name).read_text(encoding="utf-8"))
    return template.substitute(values)
