# app/routes/stocks.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

# Importamos banco, modelos e schemas
from app.database.session import get_db
from app.models.stock import StockQuote
from app.schemas.stock import StockResponse, StockCreate

# Roteador com prefixo e tag para o Swagger
router = APIRouter(
    prefix="/api/stocks",
    tags=["Cotações de Ações"]
)


# 1. Rota para REGISTRAR uma nova cotação (usada pelo Worker/Cache)
@router.post(
    "/",
    response_model=StockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nova cotação no banco (Worker/Cache)"
)
def create_stock_quote(quote_in: StockCreate, db: Session = Depends(get_db)):
    """
    Grava uma nova cotação no histórico do banco de dados.
    Normaliza o ticker para maiúsculas (ex: petr4 -> PETR4).
    """
    ticker_clean = quote_in.ticker.strip().upper()

    new_quote = StockQuote(
        ticker=ticker_clean,
        price=quote_in.price,
        open_price=quote_in.open_price,
        high_price=quote_in.high_price,
        low_price=quote_in.low_price,
        change_percent=quote_in.change_percent
    )

    db.add(new_quote)
    db.commit()
    db.refresh(new_quote)

    return new_quote


# 2. Rota para CONSULTAR o preço mais recente de um ticker
@router.get(
    "/{ticker}",
    response_model=StockResponse,
    summary="Obter cotação mais recente de uma ação"
)
def get_latest_quote(ticker: str, db: Session = Depends(get_db)):
    """
    Busca o registro mais recente gravado no banco para o ticker informado.
    """
    ticker_clean = ticker.strip().upper()

    # Busca ordenada pelo timestamp mais novo (DESC = decrescente)
    quote = (
        db.query(StockQuote)
        .filter(StockQuote.ticker == ticker_clean)
        .order_by(StockQuote.timestamp.desc())
        .first()
    )

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhuma cotação encontrada para o ticker '{ticker_clean}'."
        )

    return quote


# 3. Rota para HISTÓRICO temporal de cotações (para gráficos do Front-end)
@router.get(
    "/{ticker}/history",
    response_model=List[StockResponse],
    summary="Obter histórico de cotações para visualização gráfica"
)
def get_stock_history(
    ticker: str,
    limit: int = Query(30, ge=1, le=100, description="Quantidade máxima de pontos históricos"),
    db: Session = Depends(get_db)
):
    """
    Retorna o histórico cronológico de preços para plotagem de gráficos.
    🛡️ ge=1 e le=100 limitam a quantidade de registros, prevenindo DoS por memória.
    """
    ticker_clean = ticker.strip().upper()

    # Busca as últimas 'limit' cotações
    quotes = (
        db.query(StockQuote)
        .filter(StockQuote.ticker == ticker_clean)
        .order_by(StockQuote.timestamp.desc())
        .limit(limit)
        .all()
    )

    if not quotes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum histórico encontrado para o ticker '{ticker_clean}'."
        )

    # Invertemos para ordem cronológica (do mais antigo para o mais novo) para o gráfico
    return list(reversed(quotes))