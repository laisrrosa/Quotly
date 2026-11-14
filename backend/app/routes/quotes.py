"""Rotas de cotação do contrato do front-end (API_CONTRACT.md).

    GET /api/quotes/{ticker}
    GET /api/quotes/{ticker}/history?range=7d|1mo|6mo|1y

Buscam em APIs externas (brapi / Yahoo Finance) pelo serviço do Integrante 2.
Exigem login (JWT). São rotas `def` (não `async def`) de propósito: as
chamadas de rede são síncronas e assim rodam no threadpool do FastAPI.

Para ativar, em app/main.py:

    from app.routes.quotes import router as quotes_router
    app.include_router(quotes_router)
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.models.user import User
from app.services import market_data
from app.services.errors import (
    InvalidRangeError,
    ProviderUnavailableError,
    TickerNotFoundError,
)

router = APIRouter(prefix="/api/quotes", tags=["Cotações (mercado)"])


def _call(function, *args):
    try:
        return function(*args)
    except TickerNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except InvalidRangeError as exc:
        raise HTTPException(422, str(exc))
    except ProviderUnavailableError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))


@router.get("/{ticker}", summary="Cotação atual de um ativo")
def get_quote(ticker: str, _: User = Depends(get_current_user)):
    return _call(market_data.get_current_quote, ticker)


@router.get("/{ticker}/history", summary="Histórico de fechamentos diários")
def get_history(ticker: str, range: str = "1mo", _: User = Depends(get_current_user)):
    return _call(market_data.get_historical_quotes, ticker, range)
