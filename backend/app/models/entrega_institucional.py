from app.database import db
from datetime import datetime
from enum import Enum


class EstadoEntrega(Enum):
    """Estado da entrega institucional."""
    AGENDADA = "agendada"
    DESPACHADA = "despachada"
    RECEBIDA = "recebida"
    CANCELADA = "cancelada"


class EntregaInstitucional(db.Model):
    """
    Modelo para Entrega Institucional de Medicamentos.
    
    Representa a entrega de uma reserva para uma instituição receptora.
    """
    __tablename__ = "entregas_institucionais"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    
    # Reserva vinculada
    reserva_id = db.Column(db.Integer, db.ForeignKey("reservas_ofertas.id"), nullable=False, unique=True)
    
    # Estado da entrega
    estado = db.Column(db.String(20), nullable=False, default=EstadoEntrega.AGENDADA.value)
    
    # Despacho
    despachado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    despachado_em = db.Column(db.DateTime, nullable=True)
    
    # Recebimento
    recebido_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    recebido_em = db.Column(db.DateTime, nullable=True)
    
    # Observações
    observacoes = db.Column(db.Text, nullable=True)
    
    # Idempotência
    operacao_id = db.Column(db.String(64), unique=True, nullable=True, index=True)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relacionamentos
    reserva = db.relationship("ReservaOferta", foreign_keys=[reserva_id], lazy=True)
    despachado_por = db.relationship("Usuario", foreign_keys=[despachado_por_id], overlaps='usuario')
    recebido_por = db.relationship("Usuario", foreign_keys=[recebido_por_id], overlaps='usuario')
    
    def despachar(self, usuario_id):
        """
        Despacha a entrega (move para status DESPACHADA).
        
        Args:
            usuario_id: ID do usuário que despacha (usuário da farmácia doadora)
            
        Returns:
            bool: True se o despacho foi bem-sucedido, False caso contrário
        """
        if self.estado != EstadoEntrega.AGENDADA.value:
            return False
        
        self.estado = EstadoEntrega.DESPACHADA.value
        self.despachado_por_id = usuario_id
        self.despachado_em = datetime.utcnow()
        return True
    
    def receber(self, usuario_id, observacoes=None):
        """
        Recebe a entrega (move para status RECEBIDA).
        
        Args:
            usuario_id: ID do usuário que recebe (usuário da instituição destinatária)
            observacoes: Observações do recebimento (opcional)
            
        Returns:
            bool: True se o recebimento foi bem-sucedido, False caso contrário
        """
        if self.estado != EstadoEntrega.DESPACHADA.value:
            return False
        
        self.estado = EstadoEntrega.RECEBIDA.value
        self.recebido_por_id = usuario_id
        self.recebido_em = datetime.utcnow()
        if observacoes:
            self.observacoes = observacoes
        return True
    
    def cancelar(self):
        """
        Cancela a entrega (move para status CANCELADA).
        
        Returns:
            bool: True se o cancelamento foi bem-sucedido, False caso contrário
        """
        if self.estado not in [EstadoEntrega.AGENDADA.value, EstadoEntrega.DESPACHADA.value]:
            return False
        
        self.estado = EstadoEntrega.CANCELADA.value
        return True
    
    def __repr__(self):
        return f"<EntregaInstitucional {self.id} - {self.estado}>"
