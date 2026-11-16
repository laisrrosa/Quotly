"""Testes do serviço de cotações (sem acesso à internet: provedores simulados)."""
from datetime import date

import pytest

from app.services.errors import (
    InvalidRangeError,
    ProviderUnavailableError,
    TickerNotFoundError,
)
from app.services.market_data import MarketDataService, normalize_ticker

CONTRACT_QUOTE_FIELDS = {
    "ticker", "name", "currency", "price", "change", "changePercent",
    "previousClose", "high", "low", "volume", "updatedAt",
}


def make_quote(ticker="PETR4", price=38.42):
    return {
        "ticker": ticker, "name": "Petrobras PN", "currency": "BRL",
        "price": price, "change": 0.57, "changePercent": 1.5059,
        "previousClose": 37.85, "high": 38.9, "low": 37.6,
        "volume": 31250000, "updatedAt": "2026-10-24T18:30:00Z",
    }


class FakeProvider:
    def __init__(self, name="fake", quotes=None, history=None, error=None, supported=True):
        self.name = name
        self.quotes = quotes or {}
        self.history = history or {}
        self.error = error
        self.supported = supported
        self.calls = 0

    def supports(self, ticker):
        return self.supported

    def fetch_quote(self, ticker):
        self.calls += 1
        if self.error:
            raise self.error
        if ticker not in self.quotes:
            raise TickerNotFoundError(ticker)
        return dict(self.quotes[ticker])

    def fetch_history(self, ticker, period):
        self.calls += 1
        if self.error:
            raise self.error
        if ticker not in self.history:
            raise TickerNotFoundError(ticker)
        return list(self.history[ticker])


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


# ------------------------------------------------------------------ tickers
def test_normalize_ticker_limpa_e_coloca_em_maiusculas():
    assert normalize_ticker("  petr4 ") == "PETR4"
    assert normalize_ticker("^bvsp") == "^BVSP"
    assert normalize_ticker("brk-b") == "BRK-B"


@pytest.mark.parametrize("invalido", ["", "   ", "PETR4; DROP TABLE", "A" * 30, "../etc", None])
def test_ticker_com_formato_invalido_vira_nao_encontrado(invalido):
    with pytest.raises(TickerNotFoundError):
        normalize_ticker(invalido)


# ------------------------------------------------------------------ cotação
def test_cotacao_segue_o_contrato_e_arredonda():
    service = MarketDataService([FakeProvider(quotes={"PETR4": make_quote()})])
    quote = service.get_current_quote("petr4")
    assert set(quote) == CONTRACT_QUOTE_FIELDS
    assert quote["ticker"] == "PETR4"
    assert quote["changePercent"] == 1.51


def test_ticker_inexistente_em_todos_os_provedores():
    service = MarketDataService([FakeProvider("a"), FakeProvider("b")])
    with pytest.raises(TickerNotFoundError) as info:
        service.get_current_quote("XYZ1")
    assert str(info.value) == 'Ativo "XYZ1" não encontrado.'


def test_fallback_quando_primeiro_provedor_esta_fora():
    primeiro = FakeProvider("a", error=ProviderUnavailableError())
    segundo = FakeProvider("b", quotes={"PETR4": make_quote()})
    quote = MarketDataService([primeiro, segundo]).get_current_quote("PETR4")
    assert quote["price"] == 38.42
    assert primeiro.calls == 1 and segundo.calls == 1


def test_fallback_quando_primeiro_provedor_nao_conhece_o_ticker():
    brapi = FakeProvider("brapi")  # não tem AAPL
    yahoo = FakeProvider("yfinance", quotes={"AAPL": make_quote("AAPL", 230.1)})
    assert MarketDataService([brapi, yahoo]).get_current_quote("AAPL")["price"] == 230.1


def test_provedor_que_nao_suporta_o_ticker_nem_e_chamado():
    brapi = FakeProvider("brapi", supported=False)
    yahoo = FakeProvider("yfinance", quotes={"AAPL": make_quote("AAPL")})
    MarketDataService([brapi, yahoo]).get_current_quote("AAPL")
    assert brapi.calls == 0


def test_todos_fora_do_ar_levanta_indisponivel():
    service = MarketDataService([FakeProvider(error=ProviderUnavailableError())])
    with pytest.raises(ProviderUnavailableError):
        service.get_current_quote("PETR4")


def test_erro_inesperado_do_provedor_nao_vaza():
    service = MarketDataService([FakeProvider(error=RuntimeError("bug"))])
    with pytest.raises(ProviderUnavailableError):
        service.get_current_quote("PETR4")


# -------------------------------------------------------------------- cache
def test_cache_evita_chamadas_repetidas_e_expira():
    clock = FakeClock()
    provider = FakeProvider(quotes={"PETR4": make_quote()})
    service = MarketDataService([provider], quote_ttl=60, clock=clock)

    service.get_current_quote("PETR4")
    service.get_current_quote("PETR4")
    assert provider.calls == 1

    clock.now += 61
    service.get_current_quote("PETR4")
    assert provider.calls == 2


def test_cache_vencido_e_servido_se_provedores_cairem():
    clock = FakeClock()
    provider = FakeProvider(quotes={"PETR4": make_quote()})
    service = MarketDataService([provider], quote_ttl=60, clock=clock)
    service.get_current_quote("PETR4")

    clock.now += 600
    provider.error = ProviderUnavailableError()
    assert service.get_current_quote("PETR4")["price"] == 38.42


def test_alterar_o_resultado_nao_corrompe_o_cache():
    service = MarketDataService([FakeProvider(quotes={"PETR4": make_quote()})])
    service.get_current_quote("PETR4")["price"] = -1
    assert service.get_current_quote("PETR4")["price"] == 38.42


# ---------------------------------------------------------------- histórico
def test_historico_ordenado_sem_duplicados_e_no_formato_do_contrato():
    history = [
        {"date": "2026-10-22", "close": 37.85},
        {"date": "2026-10-20", "close": 37.1},
        {"date": "2026-10-21", "close": 37.554},
        {"date": "2026-10-21", "close": 37.554},
    ]
    service = MarketDataService([FakeProvider(history={"PETR4": history})])
    assert service.get_historical_quotes("PETR4", "1mo") == [
        {"date": "2026-10-20", "close": 37.1},
        {"date": "2026-10-21", "close": 37.55},
        {"date": "2026-10-22", "close": 37.85},
    ]


def test_historico_7d_recorta_os_ultimos_sete_dias():
    history = [{"date": f"2026-10-{day:02d}", "close": float(day)} for day in range(1, 25)]
    service = MarketDataService(
        [FakeProvider(history={"PETR4": history})], today=lambda: date(2026, 10, 24)
    )
    points = service.get_historical_quotes("PETR4", "7d")
    assert points[0]["date"] == "2026-10-17"
    assert points[-1]["date"] == "2026-10-24"


def test_periodo_invalido():
    service = MarketDataService([FakeProvider()])
    with pytest.raises(InvalidRangeError):
        service.get_historical_quotes("PETR4", "10y")


# -------------------------------------------------------------------- lote
def test_lote_remove_duplicados_e_ignora_falhas():
    provider = FakeProvider(quotes={"PETR4": make_quote(), "VALE3": make_quote("VALE3", 61.0)})
    service = MarketDataService([provider])
    quotes = service.get_current_quotes(["PETR4", "VALE3", "PETR4", "NADA1"])
    assert set(quotes) == {"PETR4", "VALE3"}
    assert provider.calls == 3  # PETR4 uma vez só + VALE3 + NADA1
