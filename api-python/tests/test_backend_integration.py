"""Integração com o back-end real (modelos, sessão e rotas do Integrante 1).

Ignorado automaticamente se este módulo for usado fora da pasta `api-python/`.
"""
import pytest

pytest.importorskip("app.database.session")
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from app.core.security import create_access_token, get_password_hash  # noqa: E402
from app.database.session import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Alert, StockQuote, User  # noqa: E402
from app.services import market_data  # noqa: E402
from app.services.errors import TickerNotFoundError  # noqa: E402
from app.workers.alert_monitor import AlertMonitor  # noqa: E402
from app.workers.alert_repository import build_default_repository  # noqa: E402

try:  # a rota de cotações é um arquivo novo: só testa se já foi adicionada ao app
    from app.routes.quotes import router as quotes_router  # noqa: E402
except ImportError:  # pragma: no cover
    quotes_router = None


@pytest.fixture(autouse=True)
def fresh_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def user():
    with SessionLocal() as db:
        db.add(User(name="Maria", email="maria@email.com", hashed_password=get_password_hash("12345678")))
        db.commit()
    return "maria@email.com"


@pytest.fixture
def auth(user):
    return {"Authorization": f"Bearer {create_access_token(user)}"}


@pytest.fixture
def client():
    if quotes_router is not None and not any(
        getattr(r, "path", "").startswith("/api/quotes") for r in app.routes
    ):
        app.include_router(quotes_router)
    return TestClient(app)


class FakeProvider:
    name = "fake"

    def supports(self, ticker):
        return True

    def fetch_quote(self, ticker):
        if ticker == "NADA1":
            raise TickerNotFoundError(ticker)
        return {
            "ticker": ticker, "name": "Petrobras PN", "currency": "BRL", "price": 38.42,
            "change": 0.57, "changePercent": 1.51, "previousClose": 37.85,
            "high": 38.9, "low": 37.6, "volume": 31250000, "updatedAt": "2026-10-24T18:30:00Z",
        }

    def fetch_history(self, ticker, period):
        if ticker == "NADA1":
            raise TickerNotFoundError(ticker)
        return [{"date": "2026-10-20", "close": 37.1}, {"date": "2026-10-21", "close": 37.55}]


@pytest.fixture
def fake_market(monkeypatch):
    service = market_data.MarketDataService([FakeProvider()])
    monkeypatch.setattr(market_data, "_default_service", service)
    return service


# ------------------------------------------------------------------ worker
def test_worker_dispara_alerta_criado_pela_api(client, auth, fake_market):
    created = client.post(
        "/api/alerts/", headers=auth,
        json={"ticker": "petr4", "target_price": 38.0, "condition": "ABOVE"},
    )
    assert created.status_code == 201

    emails = []
    monitor = AlertMonitor(
        build_default_repository(), send_email=lambda **kwargs: emails.append(kwargs)
    )
    result = monitor.run_cycle()

    assert (result.checked, result.triggered, result.email_failures) == (1, 1, 0)
    assert emails[0]["to_email"] == "maria@email.com"
    assert emails[0]["user_name"] == "Maria"
    assert emails[0]["condition"] == "above" and emails[0]["current_price"] == 38.42

    listed = client.get("/api/alerts/", headers=auth).json()
    assert listed[0]["is_triggered"] is True

    assert monitor.run_cycle().triggered == 0  # não reenvia
    assert len(emails) == 1


def test_worker_nao_dispara_alerta_desativado_pelo_usuario(client, auth, fake_market):
    alert = client.post(
        "/api/alerts/", headers=auth,
        json={"ticker": "PETR4", "target_price": 10, "condition": "ABOVE"},
    ).json()
    client.patch(f"/api/alerts/{alert['id']}", headers=auth, json={"is_active": False})

    emails = []
    result = AlertMonitor(
        build_default_repository(), send_email=lambda **kwargs: emails.append(kwargs)
    ).run_cycle()
    assert result.checked == 0 and emails == []


def test_worker_grava_cotacao_que_alimenta_rota_stocks(client, auth, fake_market):
    client.post("/api/alerts/", headers=auth, json={"ticker": "PETR4", "target_price": 99, "condition": "ABOVE"})
    AlertMonitor(build_default_repository(), send_email=lambda **kw: None).run_cycle()

    with SessionLocal() as db:
        saved = db.query(StockQuote).all()
    assert [(q.ticker, q.price, q.high_price, q.low_price) for q in saved] == [("PETR4", 38.42, 38.9, 37.6)]

    response = client.get("/api/stocks/PETR4")
    assert response.status_code == 200
    assert response.json()["price"] == 38.42


# ------------------------------------------------------------- rotas quotes
@pytest.mark.skipif(quotes_router is None, reason="app/routes/quotes.py não encontrado")
class TestQuotesRoutes:
    def test_exige_login(self, client, fake_market):
        assert client.get("/api/quotes/PETR4").status_code == 401

    def test_cotacao_no_formato_do_contrato(self, client, auth, fake_market):
        response = client.get("/api/quotes/petr4", headers=auth)
        assert response.status_code == 200
        assert set(response.json()) == {
            "ticker", "name", "currency", "price", "change", "changePercent",
            "previousClose", "high", "low", "volume", "updatedAt",
        }

    def test_historico(self, client, auth, fake_market):
        response = client.get("/api/quotes/PETR4/history?range=7d", headers=auth)
        assert response.json() == [
            {"date": "2026-10-20", "close": 37.1},
            {"date": "2026-10-21", "close": 37.55},
        ]

    def test_ticker_inexistente_404_em_portugues(self, client, auth, fake_market):
        response = client.get("/api/quotes/NADA1", headers=auth)
        assert response.status_code == 404
        assert response.json() == {"detail": 'Ativo "NADA1" não encontrado.'}

    def test_periodo_invalido_422(self, client, auth, fake_market):
        assert client.get("/api/quotes/PETR4/history?range=10y", headers=auth).status_code == 422
