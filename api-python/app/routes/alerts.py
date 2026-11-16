from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.session import get_db
from app.models.user import User
from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertUpdate, AlertResponse
from app.core.deps import get_current_user

router = APIRouter(
    prefix="/api/alerts",
    tags=["Alertas"]
)

@router.post(
    "/",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar um novo alerta de preço"
)
def create_alert(
    alert_in: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    new_alert = Alert(
        user_id=current_user.id,
        ticker=alert_in.ticker,
        target_price=alert_in.target_price,
        condition=alert_in.condition,
        is_triggered=False,
        is_active=True
    )

    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)

    return new_alert

@router.get(
    "/",
    response_model=List[AlertResponse],
    summary="Listar todos os alertas do usuário logado"
)
def list_my_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    alerts = db.query(Alert).filter(Alert.user_id == current_user.id).all()
    return alerts

@router.patch(
    "/{alert_id}",
    response_model=AlertResponse,
    summary="Atualizar um alerta existente"
)
def update_alert(
    alert_id: int,
    alert_in: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta não encontrado."
        )

    if alert_in.target_price is not None:
        alert.target_price = alert_in.target_price
    if alert_in.condition is not None:
        alert.condition = alert_in.condition
    if alert_in.is_active is not None:
        alert.is_active = alert_in.is_active

    db.commit()
    db.refresh(alert)
    return alert

@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir um alerta"
)
def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta não encontrado."
        )

    db.delete(alert)
    db.commit()

    return None