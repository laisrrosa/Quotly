from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Literal

class AlertBase(BaseModel):

    ticker: str = Field(..., min_length=4, max_length=8, description="Código da ação (ex: PETR4, VALE3)")
    target_price: float = Field(..., gt=0, description="Preço alvo (deve ser maior que zero)")
    condition: Literal["ABOVE", "BELOW"] = Field(..., description="Condição de disparo: ABOVE (dispara quando o valor esta acima) ou BELOW (dispara quando o valor esta abaixo)")

    @field_validator("ticker")
    @classmethod
    def format_ticker(cls, v: str) -> str:
        return v.strip().upper()
    # converte os tickers para maiúsculo e tira os espaços
    
class AlertCreate(AlertBase):
    pass

class AlertUpdate(BaseModel):
    target_price: float | None = Field(None, gt=0)
    condition: Literal["ABOVE", "BELOW"] | None = None
    is_active: bool | None = None

class AlertResponse(AlertBase):
    id: int
    user_id: int
    is_triggered: bool
    is_active: bool
    created_at: datetime
    model_config = {
        "from_attributes": True
    }