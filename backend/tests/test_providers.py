"""Testes dos provedores com respostas HTTP / yfinance simuladas."""
import sys
import types

import httpx
import pandas as pd
import pytest

from app.services.errors import ProviderUnavailableError, TickerNotFoundError
from app.services.providers import BrapiProvider, YFinanceProvider

BRAPI_QUOTE = {
    "results": [
        {
            "requestedSymbol": "PETR4",
            "symbol": "PETR4",
            "changed": False,
            "data": {
                "shortName": "PETROBRAS PN",
                "currency": "BRL",
                "regularMarketPrice": 38.42,
                "regularMarketDayHigh": 38.9,
                "regularMarketDayLow": 37.6,
                "regularMarketChange": 0.57,
                "regularMarketChangePercent": 1.51,
                "regularMarketTime": "2026-10-24T18:30:00.000Z",
                "regularMarketVolume": 31250000,
                "regularMarketPreviousClose": 37.85,
            },
        }
    ]
}

BRAPI_HISTORY = {
    "results": [
        {
            "symbol": "PETR4",
            "data": {
                "historicalDataPrice": [
                    {"date": 1792497600, "close": 37.1},  # 2026-10-20
                    {"date": 1792584000, "close": 37.55},  # 2026-10-21
                    {"date": 1792670400, "close": None},
                ]
            },
        }
    ]
}


def brapi_with(handler, **kwargs):
    client = httpx.Client(base_url="https://brapi.test", transport=httpx.MockTransport(handler))
    return BrapiProvider(token="tok", client=client, backoff_seconds=0, **kwargs)


# -------------------------------------------------------------------- brapi
def test_brapi_cotacao_normalizada():
    seen = {}

    def handler(request):
        seen["url"] = str(request.url)
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json=BRAPI_QUOTE)

    quote = brapi_with(handler).fetch_quote("PETR4")
    assert seen["url"] == "https://brapi.test/api/v2/stocks/quote?symbols=PETR4"
    assert seen["auth"] == "Bearer tok"
    assert quote == {
        "ticker": "PETR4", "name": "PETROBRAS PN", "currency": "BRL",
        "price": 38.42, "change": 0.57, "changePercent": 1.51,
        "previousClose": 37.85, "high": 38.9, "low": 37.6,
        "volume": 31250000, "updatedAt": "2026-10-24T18:30:00Z",
    }


def test_brapi_historico():
    points = brapi_with(lambda r: httpx.Response(200, json=BRAPI_HISTORY)).fetch_history("PETR4", "1mo")
    assert points == [
        {"date": "2026-10-20", "close": 37.1},
        {"date": "2026-10-21", "close": 37.55},
    ]


@pytest.mark.parametrize(
    "response",
    [httpx.Response(404, json={"error": True}), httpx.Response(200, json={"results": []})],
)
def test_brapi_ticker_inexistente(response):
    with pytest.raises(TickerNotFoundError):
        brapi_with(lambda r: response).fetch_quote("XYZ1")


def test_brapi_rate_limit_tenta_de_novo_e_desiste():
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(429, json={"error": True})

    with pytest.raises(ProviderUnavailableError):
        brapi_with(handler, max_retries=2).fetch_quote("PETR4")
    assert len(calls) == 3


def test_brapi_recupera_apos_falha_temporaria():
    responses = iter([httpx.Response(503), httpx.Response(200, json=BRAPI_QUOTE)])
    assert brapi_with(lambda r: next(responses)).fetch_quote("PETR4")["price"] == 38.42


def test_brapi_erro_de_rede_vira_indisponivel():
    def handler(request):
        raise httpx.ConnectError("sem rede")

    with pytest.raises(ProviderUnavailableError):
        brapi_with(handler).fetch_quote("PETR4")


@pytest.mark.parametrize("status", [400, 401, 403])
def test_brapi_recusa_por_plano_ou_token_nao_repete(status):
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(status, json={"error": True})

    with pytest.raises(ProviderUnavailableError):
        brapi_with(handler).fetch_history("PETR4", "1y")
    assert len(calls) == 1


def test_brapi_so_atende_tickers_da_b3():
    provider = brapi_with(lambda r: httpx.Response(200, json=BRAPI_QUOTE))
    assert provider.supports("PETR4") and provider.supports("BOVA11")
    assert not provider.supports("AAPL")


# ----------------------------------------------------------------- yfinance
@pytest.fixture
def fake_yfinance(monkeypatch):
    """Substitui o módulo `yfinance` por um falso controlado pelo teste."""
    state = {"frame": pd.DataFrame(), "meta": {}, "error": None, "symbols": []}

    class FakeTicker:
        def __init__(self, symbol):
            state["symbols"].append(symbol)

        def history(self, **kwargs):
            if state["error"]:
                raise state["error"]
            return state["frame"]

        @property
        def history_metadata(self):
            return state["meta"]

    monkeypatch.setitem(sys.modules, "yfinance", types.SimpleNamespace(Ticker=FakeTicker))
    return state


def frame(rows):
    index = pd.DatetimeIndex([r[0] for r in rows], tz="America/Sao_Paulo")
    return pd.DataFrame(
        {
            "Close": [r[1] for r in rows],
            "High": [r[1] + 0.5 for r in rows],
            "Low": [r[1] - 0.5 for r in rows],
            "Volume": [1000 * (i + 1) for i in range(len(rows))],
        },
        index=index,
    )


def test_yfinance_cotacao(fake_yfinance):
    fake_yfinance["frame"] = frame([("2026-10-22", 37.85), ("2026-10-23", float("nan")), ("2026-10-24", 38.42)])
    fake_yfinance["meta"] = {"shortName": "PETROBRAS PN", "currency": "BRL", "regularMarketTime": 1792866600}

    quote = YFinanceProvider().fetch_quote("PETR4")
    assert fake_yfinance["symbols"] == ["PETR4.SA"]
    assert quote["ticker"] == "PETR4"
    assert quote["name"] == "PETROBRAS PN"
    assert quote["price"] == 38.42
    assert quote["previousClose"] == 37.85  # pula a linha com NaN
    assert quote["change"] == pytest.approx(0.57)
    assert quote["changePercent"] == pytest.approx(1.5059, abs=1e-3)
    assert quote["volume"] == 3000
    assert quote["updatedAt"].endswith("Z")


def test_yfinance_ticker_americano_fica_sem_sufixo(fake_yfinance):
    fake_yfinance["frame"] = frame([("2026-10-24", 230.0)])
    quote = YFinanceProvider().fetch_quote("AAPL")
    assert fake_yfinance["symbols"] == ["AAPL"]
    assert quote["currency"] == "USD" and quote["name"] == "AAPL"


def test_yfinance_historico(fake_yfinance):
    fake_yfinance["frame"] = frame([("2026-10-20", 37.1), ("2026-10-21", 37.55)])
    assert YFinanceProvider().fetch_history("PETR4", "1mo") == [
        {"date": "2026-10-20", "close": 37.1},
        {"date": "2026-10-21", "close": 37.55},
    ]


def test_yfinance_dataframe_vazio_e_ticker_inexistente(fake_yfinance):
    with pytest.raises(TickerNotFoundError):
        YFinanceProvider().fetch_quote("XYZ1")


def test_yfinance_excecao_vira_indisponivel(fake_yfinance):
    fake_yfinance["error"] = ConnectionError("rate limited")
    with pytest.raises(ProviderUnavailableError):
        YFinanceProvider().fetch_history("PETR4", "1y")
