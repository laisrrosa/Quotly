from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone

from app.database.session import Base


class StockQuote(Base):

    __tablename__ = "stock_quotes"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(8), nullable=False, index=True)
    price = Column(Float, nullable=False)
    # Guarda o ultimo preço pesquisado, salvando o valor do ativo no fechamento do pregão
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    # Open, high e low price é para fazer o monitoramento do dia do ativo, para futuras implementações de gráficos de avaliação de ativos
    change_percent = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)