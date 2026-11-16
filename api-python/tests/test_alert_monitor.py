"""Testes da lógica do worker de alertas (banco, cotações e e-mail simulados)."""
from datetime import datetime, timezone

import pytest

from app.workers.alert_monitor import AlertMonitor, PendingAlert, is_condition_met

NOW = datetime(2026, 10, 24, 18, 30, tzinfo=timezone.utc)


class InMemoryRepository:
    def __init__(self, alerts):
        self.alerts = {a.id: a for a in alerts}
        self.triggered = {}
        self.released = []

    def list_pending(self):
        return [a for a in self.alerts.values() if a.id not in self.triggered]

    def mark_triggered(self, alert_id, triggered_at):
        if alert_id in self.triggered:
            return False
        self.triggered[alert_id] = triggered_at
        return True

    def release(self, alert_id):
        self.triggered.pop(alert_id, None)
        self.released.append(alert_id)


class Harness:
    def __init__(self, alerts, prices, email_error=None):
        self.repository = InMemoryRepository(alerts)
        self.prices = prices
        self.email_error = email_error
        self.requested_tickers = []
        self.emails = []
        self.monitor = AlertMonitor(
            self.repository, self.fetch_quotes, self.send_email, now=lambda: NOW
        )

    def fetch_quotes(self, tickers):
        self.requested_tickers.append(list(tickers))
        return {
            t: {"ticker": t, "price": self.prices[t], "currency": "BRL"}
            for t in tickers
            if t in self.prices
        }

    def send_email(self, **kwargs):
        if self.email_error:
            raise self.email_error
        self.emails.append(kwargs)


def alert(id, ticker="PETR4", target=40.0, condition="above", email="maria@email.com"):
    return PendingAlert(id, ticker, target, condition, email, "Maria")


@pytest.mark.parametrize(
    "condition, current, target, expected",
    [
        ("above", 40.01, 40.0, True),
        ("above", 40.0, 40.0, True),  # igual ao alvo também dispara
        ("above", 39.99, 40.0, False),
        ("below", 29.99, 30.0, True),
        ("below", 30.0, 30.0, True),
        ("below", 30.01, 30.0, False),
    ],
)
def test_is_condition_met(condition, current, target, expected):
    assert is_condition_met(condition, current, target) is expected


def test_dispara_envia_email_e_marca_no_banco():
    h = Harness([alert(1, target=38.0)], {"PETR4": 38.5})
    result = h.monitor.run_cycle()

    assert (result.checked, result.triggered, result.email_failures) == (1, 1, 0)
    assert h.repository.triggered == {1: NOW}
    assert h.emails == [
        dict(
            to_email="maria@email.com", user_name="Maria", ticker="PETR4",
            condition="above", target_price=38.0, current_price=38.5,
            currency="BRL", triggered_at=NOW,
        )
    ]


def test_nao_dispara_se_condicao_nao_foi_atingida():
    h = Harness([alert(1, target=40.0), alert(2, target=30.0, condition="below")], {"PETR4": 38.5})
    result = h.monitor.run_cycle()
    assert result.checked == 2 and result.triggered == 0
    assert h.emails == [] and h.repository.triggered == {}


def test_consulta_cada_ticker_uma_unica_vez():
    alerts = [alert(1), alert(2, target=50.0), alert(3, ticker="vale3"), alert(4, ticker="VALE3")]
    h = Harness(alerts, {"PETR4": 10.0, "VALE3": 10.0})
    result = h.monitor.run_cycle()
    assert h.requested_tickers == [["PETR4", "VALE3"]]
    assert result.tickers == 2 and result.checked == 4


def test_alerta_disparado_nao_envia_email_de_novo():
    h = Harness([alert(1, target=38.0)], {"PETR4": 38.5})
    h.monitor.run_cycle()
    h.monitor.run_cycle()
    assert len(h.emails) == 1


def test_falha_no_email_devolve_alerta_para_ativo_e_tenta_no_proximo_ciclo():
    h = Harness([alert(1, target=38.0)], {"PETR4": 38.5}, email_error=RuntimeError("smtp fora"))
    result = h.monitor.run_cycle()
    assert result.triggered == 0 and result.email_failures == 1
    assert h.repository.triggered == {} and h.repository.released == [1]

    h.email_error = None
    assert h.monitor.run_cycle().triggered == 1
    assert len(h.emails) == 1


def test_alerta_ja_marcado_por_outro_worker_nao_envia_email():
    h = Harness([alert(1, target=38.0)], {"PETR4": 38.5})
    h.repository.mark_triggered = lambda alert_id, triggered_at: False
    assert h.monitor.run_cycle().triggered == 0
    assert h.emails == []


def test_ticker_sem_cotacao_e_pulado_sem_afetar_os_outros():
    h = Harness([alert(1, ticker="NADA1"), alert(2, target=38.0)], {"PETR4": 38.5})
    result = h.monitor.run_cycle()
    assert result.tickers_without_quote == ["NADA1"]
    assert result.checked == 1 and result.triggered == 1


def test_alerta_com_problema_nao_interrompe_os_demais():
    h = Harness([alert(1, condition="invalida"), alert(2, target=38.0)], {"PETR4": 38.5})
    result = h.monitor.run_cycle()
    assert result.triggered == 1 and result.error is None


def test_sem_alertas_nao_consulta_cotacoes():
    h = Harness([], {})
    assert h.monitor.run_cycle().checked == 0
    assert h.requested_tickers == []


def test_falha_no_banco_ou_nas_cotacoes_nao_derruba_o_worker():
    h = Harness([alert(1)], {"PETR4": 50.0})

    def broken(tickers):
        raise ConnectionError("rede fora")

    h.monitor._fetch_quotes = broken
    result = h.monitor.run_cycle()  # não levanta exceção
    assert "ConnectionError" in result.error
    assert h.emails == []
