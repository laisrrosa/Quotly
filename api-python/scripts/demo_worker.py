"""Demonstração do worker sem depender do back-end (Integrante 1).

Cria um banco SQLite temporário em memória com um usuário e dois alertas e
executa um ciclo do monitor com cotações reais:

    python -m scripts.demo_worker voce@email.com
    python -m scripts.demo_worker voce@email.com --ticker VALE3

Um dos alertas é montado para disparar com certeza (alvo abaixo do preço
atual, condição "above"), então o e-mail é enviado (ou só logado, se
EMAIL_BACKEND=console).
"""
import argparse
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.logging_config import setup_logging
from app.services import market_data
from app.services.errors import MarketDataError
from app.workers.alert_monitor import AlertMonitor
from app.workers.alert_repository import SqlAlchemyAlertRepository


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
    status: Mapped[str] = mapped_column(String(10), default="active")
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("to_email")
    parser.add_argument("--ticker", default="PETR4")
    args = parser.parse_args()
    setup_logging()

    try:
        price = market_data.get_current_quote(args.ticker)["price"]
    except MarketDataError as exc:
        raise SystemExit(f"Erro ao buscar a cotação: {exc}")

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine)
    with Session() as session:
        session.add(User(id=1, name="Usuário Demo", email=args.to_email))
        session.add_all([
            # dispara: o preço atual já está acima do alvo
            Alert(id=1, user_id=1, ticker=args.ticker, target_price=round(price * 0.95, 2), condition="above"),
            # não dispara: o preço teria que dobrar
            Alert(id=2, user_id=1, ticker=args.ticker, target_price=round(price * 2, 2), condition="above"),
        ])
        session.commit()

    result = AlertMonitor(SqlAlchemyAlertRepository(Session, Alert, User)).run_cycle()

    print(f"\n{args.ticker} está em {price:.2f}")
    with Session() as session:
        for alert in session.query(Alert).order_by(Alert.id):
            print(f"  alerta {alert.id}: {alert.condition} {alert.target_price:.2f} -> {alert.status}")
    print(f"Resumo do ciclo: {result}")


if __name__ == "__main__":
    main()
