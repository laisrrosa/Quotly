"""Testes do repositório com SQLite em memória, nos dois formatos de tabela."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

from app.workers.alert_monitor import AlertMonitor
from app.workers.alert_repository import SqlAlchemyAlertRepository, normalize_condition

NOW = datetime(2026, 10, 24, 18, 30, tzinfo=timezone.utc)


def contract_models():
    """Formato do API_CONTRACT.md: `status` + `triggered_at`."""

    class Base(DeclarativeBase):
        pass

    class User(Base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(100))
        email: Mapped[str] = mapped_column(String(200))

    class Alert(Base):
        __tablename__ = "alerts"
        id: Mapped[int] = mapped_column(primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
        ticker: Mapped[str] = mapped_column(String(15))
        target_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
        condition: Mapped[str] = mapped_column(String(10))
        status: Mapped[str] = mapped_column(String(10), default="active")
        triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def is_pending(alert):
        return alert.status == "active"

    return Base, User, Alert, dict(status="active"), dict(status="disabled"), is_pending


def workflow_models():
    """Formato do workflow do Integrante 1: `is_triggered` + `is_active`."""

    class Base(DeclarativeBase):
        pass

    class User(Base):
        __tablename__ = "users"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(100))
        email: Mapped[str] = mapped_column(String(200))

    class Alert(Base):
        __tablename__ = "alerts"
        id: Mapped[int] = mapped_column(primary_key=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
        ticker: Mapped[str] = mapped_column(String(15))
        target_price: Mapped[float] = mapped_column()
        condition: Mapped[str] = mapped_column(String(10))
        is_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
        is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def is_pending(alert):
        return alert.is_active and not alert.is_triggered

    return (
        Base, User, Alert,
        dict(is_triggered=False, is_active=True),
        dict(is_triggered=False, is_active=False),
        is_pending,
    )


@pytest.fixture(params=[contract_models, workflow_models], ids=["contrato", "workflow"])
def db(request):
    Base, User, Alert, active, disabled, is_pending = request.param()
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine)

    with Session() as session:
        session.add_all([
            User(id=1, name="Maria", email="maria@email.com"),
            User(id=2, name="João", email="joao@email.com"),
        ])
        session.add_all([
            Alert(id=1, user_id=1, ticker="petr4", target_price=40, condition="ABOVE", **active),
            Alert(id=2, user_id=2, ticker="VALE3", target_price=55.5, condition="below", **active),
            Alert(id=3, user_id=1, ticker="ITUB4", target_price=30, condition="above", **disabled),
        ])
        session.commit()

    def get(alert_id):
        with Session() as session:
            return session.get(Alert, alert_id)

    repository = SqlAlchemyAlertRepository(Session, Alert, User)
    return repository, get, is_pending


def test_lista_so_pendentes_com_dados_do_usuario(db):
    repository, _, _ = db
    pending = repository.list_pending()
    assert [(a.id, a.ticker, a.target_price, a.condition, a.user_email, a.user_name) for a in pending] == [
        (1, "PETR4", 40.0, "above", "maria@email.com", "Maria"),
        (2, "VALE3", 55.5, "below", "joao@email.com", "João"),
    ]
    assert isinstance(pending[0].target_price, float)


def test_mark_triggered_so_funciona_uma_vez(db):
    repository, get, is_pending = db
    assert repository.mark_triggered(1, NOW) is True
    assert repository.mark_triggered(1, NOW) is False  # segundo worker não dispara de novo
    assert not is_pending(get(1))
    assert [a.id for a in repository.list_pending()] == [2]
    if hasattr(get(1), "triggered_at"):
        assert get(1).triggered_at is not None


def test_mark_triggered_ignora_alerta_desativado(db):
    repository, get, is_pending = db
    assert repository.mark_triggered(3, NOW) is False
    assert not is_pending(get(3))


def test_release_devolve_para_pendente(db):
    repository, get, is_pending = db
    repository.mark_triggered(1, NOW)
    repository.release(1)
    assert is_pending(get(1))
    if hasattr(get(1), "triggered_at"):
        assert get(1).triggered_at is None


def test_ciclo_completo_com_banco_real(db):
    repository, get, is_pending = db
    emails = []
    monitor = AlertMonitor(
        repository,
        fetch_quotes=lambda tickers: {
            "PETR4": {"price": 41.0, "currency": "BRL"},
            "VALE3": {"price": 60.0, "currency": "BRL"},
        },
        send_email=lambda **kwargs: emails.append(kwargs),
    )
    result = monitor.run_cycle()
    assert result.triggered == 1
    assert [e["to_email"] for e in emails] == ["maria@email.com"]
    assert not is_pending(get(1)) and is_pending(get(2))

    assert monitor.run_cycle().triggered == 0  # não reenvia
    assert len(emails) == 1


def test_normalize_condition():
    assert normalize_condition("ABOVE") == "above"
    assert normalize_condition(" Below ") == "below"
    with pytest.raises(ValueError):
        normalize_condition("igual")
