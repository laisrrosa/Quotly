"""Testes do serviço de e-mail (SMTP simulado: nada é enviado de verdade)."""
import smtplib
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.core.worker_config import get_settings
from app.services import email_service
from app.services.email_service import build_alert_email, format_price, send_email
from app.services.errors import EmailSendError


@pytest.fixture
def settings():
    return replace(
        get_settings(),
        email_backend="smtp", smtp_host="smtp.test", smtp_port=587,
        smtp_user="user", smtp_password="pass", smtp_use_tls=True, smtp_use_ssl=False,
        email_from="alertas@quotly.test", email_from_name="Quotly",
        app_url="http://localhost:5173", display_timezone="America/Sao_Paulo",
    )


def build(settings, **overrides):
    params = dict(
        to_email="maria@email.com", user_name="Maria", ticker="petr4",
        condition="above", target_price=38.0, current_price=38.5,
        triggered_at=datetime(2026, 10, 24, 18, 30, tzinfo=timezone.utc),
        settings=settings,
    )
    params.update(overrides)
    return build_alert_email(**params)


def parts(message):
    text = message.get_body(preferencelist=("plain",)).get_content()
    html = message.get_body(preferencelist=("html",)).get_content()
    return text, html


def test_format_price():
    assert format_price(38.5) == "R$ 38,50"
    assert format_price(1234.5, "USD") == "US$ 1.234,50"
    assert format_price(10, "GBP") == "GBP 10,00"


def test_assunto_e_cabecalhos(settings):
    message = build(settings)
    assert message["Subject"] == "[Quotly] Alerta de Preço: PETR4 atingiu R$ 38,50"
    assert message["To"] == "maria@email.com"
    assert message["From"] == "Quotly <alertas@quotly.test>"


def test_corpo_tem_texto_puro_e_html_com_os_detalhes(settings):
    text, html = parts(build(settings))
    for body in (text, html):
        assert "Maria" in body
        assert "PETR4" in body
        assert "subiu acima de" in body
        assert "R$ 38,00" in body and "R$ 38,50" in body
        assert "24/10/2026 às 15:30" in body  # 18:30 UTC no horário de Brasília
        assert "http://localhost:5173/alerts" in body
        assert "$" not in body.replace("R$", "")  # nenhum marcador sem preencher


def test_condicao_below(settings):
    text, _ = parts(build(settings, condition="BELOW", target_price=37.5, current_price=37.4))
    assert "caiu abaixo de R$ 37,50" in text


def test_condicao_invalida(settings):
    with pytest.raises(ValueError):
        build(settings, condition="igual")


def test_html_escapa_dados_do_usuario(settings):
    text, html = parts(build(settings, user_name="<script>alert(1)</script>"))
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


class FakeSMTP:
    instances = []

    def __init__(self, host, port, timeout=None):
        self.host, self.port = host, port
        self.events = []
        FakeSMTP.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.events.append("quit")

    def starttls(self, context=None):
        self.events.append("starttls")

    def login(self, user, password):
        self.events.append(("login", user, password))

    def send_message(self, message):
        self.events.append(("send", message["To"]))


def test_envio_smtp_com_starttls_e_login(settings, monkeypatch):
    FakeSMTP.instances.clear()
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
    send_email(build(settings), settings)

    server = FakeSMTP.instances[0]
    assert (server.host, server.port) == ("smtp.test", 587)
    assert server.events == ["starttls", ("login", "user", "pass"), ("send", "maria@email.com"), "quit"]


def test_falha_de_smtp_vira_email_send_error(settings, monkeypatch):
    class BrokenSMTP(FakeSMTP):
        def login(self, user, password):
            raise smtplib.SMTPAuthenticationError(535, b"credenciais invalidas")

    monkeypatch.setattr(email_service.smtplib, "SMTP", BrokenSMTP)
    with pytest.raises(EmailSendError):
        send_email(build(settings), settings)


def test_servidor_inacessivel_vira_email_send_error(settings, monkeypatch):
    def refuse(*args, **kwargs):
        raise ConnectionRefusedError("sem conexão")

    monkeypatch.setattr(email_service.smtplib, "SMTP", refuse)
    with pytest.raises(EmailSendError):
        send_email(build(settings), settings)


def test_backend_console_nao_abre_conexao(settings, monkeypatch):
    def explode(*args, **kwargs):
        raise AssertionError("não deveria conectar")

    monkeypatch.setattr(email_service.smtplib, "SMTP", explode)
    send_email(build(settings), replace(settings, email_backend="console"))


def test_smtp_sem_host_configurado(settings):
    with pytest.raises(EmailSendError):
        send_email(build(settings), replace(settings, smtp_host=""))
