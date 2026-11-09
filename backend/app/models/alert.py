from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database.session import Base


class Alert(Base):

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ticker = Column(String(8), nullable=False, index=True) 
    # Oito caracteres porque é o máximo de caracteres que um ativo tem hoje, caso aumente, alterar aqui
    target_price = Column(Float, nullable=False)
    condition = Column(String(10), nullable=False)
    # condição para atribuir ao target_price
    is_triggered = Column(Boolean, default=False)
    # Salvar o estado do alerta, caso o alerta seja emitido, esse booleano vai alterar apenas e desativar o monitormamento desse alerta
    is_active = Column(Boolean, default=True)
    # Flag semelhante a de um alarme de relógio, o usuário pode ligar ou desligar conforme o desejo de monitoramento
    # Essa flag é alterada para false sempre que o alerta for acionado
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    # Importante para controle do usuário
    owner = relationship("User", back_populates="alerts")