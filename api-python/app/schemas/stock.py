from pydantic import BaseModel, Field
from datetime import datetime

class StockResponse(BaseModel):
    ticker: str
    price: float
    open_price: float | None = None
    high_price: float | None = None
    low_price: float | None = None
    change_percent: float | None = None
    timestamp: datetime

    model_config = {
        "from_attributes": True
    }

class StockCreate(BaseModel):
    ticker: str = Field(..., min_length=4, max_length=8)
    price: float = Field(..., gt=0)
    open_price: float | None = None
    high_price: float | None = None
    low_price: float | None = None
    change_percent: float | None = None