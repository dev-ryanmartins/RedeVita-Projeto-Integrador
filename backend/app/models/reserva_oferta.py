from app.database import db
from datetime import datetime
from enum import Enum


class StatusReserva(Enum):
    """Status da reserva de oferta."""
    RESERVADA = "reservada"
    APROVADA = "aprovada"
    CONFIRMADA = "confirmada"
    DESPACHADA = "despachada"
    CANCELADA = "cancelada"
    EXPIRADA = "expirada"
    REJEITADA = "rejeitada"


class ReservaOferta(db.Model):
    """
    Modelo para Reserva de Oferta de Medicamento.
    
    Representa uma reserva de uma oferta por uma instituição receptora.
    A reserva bloqueia a quantidade temporariamente sem reduzir o estoque físico.
    """
    __tablename__ = "reservas_ofertas"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    
    # Oferta sendo reservada
    oferta_id = db.Column(db.Integer, db.ForeignKey("ofertas_medicamentos.id"), nullable=False)
    
    # Instituição receptora
    instituicao_id = db.Column(db.Integer, db.ForeignKey("instituicoes.id"), nullable=False)
    
    # Quantidade reservada
    quantidade_reservada = db.Column(db.Integer, nullable=False)
    
    # Status da reserva
    status = db.Column(db.String(20), nullable=False, default=StatusReserva.RESERVADA.value)
    
    # Responsável pela reserva
    reservado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    
    # Responsável pela confirmação/rejeição (farmácia doadora)
    confirmado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    confirmado_em = db.Column(db.DateTime, nullable=True)
    
    # Data de expiração da reserva (para cancelamento automático)
    data_expiracao = db.Column(db.DateTime, nullable=True)
    
    # Observações
    observacoes = db.Column(db.Text, nullable=True)
    
    # Idempotência
    operacao_id = db.Column(db.String(64), unique=True, nullable=True, index=True)
    
    # Relacionamentos
    oferta = db.relationship("OfertaMedicamento", foreign_keys=[oferta_id], lazy=True)
    instituicao = db.relationship("Instituicao", foreign_keys=[instituicao_id], lazy=True)
    reservado_por = db.relationship("Usuario", foreign_keys=[reservado_por_id], overlaps='usuario')
    confirmado_por = db.relationship("Usuario", foreign_keys=[confirmado_por_id], overlaps='usuario')
    
    def confirmar(self, usuario_id):
        """
        Confirma a reserva (move para status CONFIRMADA).
        
        Args:
            usuario_id: ID do usuário que confirma (usuário da farmácia doadora)
            
        Returns:
            bool: True se a confirmação foi bem-sucedida, False caso contrário
        """
        if self.status != StatusReserva.APROVADA.value:
            return False
        
        self.status = StatusReserva.CONFIRMADA.value
        self.confirmado_por_id = usuario_id
        self.confirmado_em = datetime.utcnow()
        return True
    
    def aprovar(self):
        """
        Aprova a reserva (move para status APROVADA).
        
        Returns:
            bool: True se a aprovação foi bem-sucedida, False caso contrário
        """
        if self.status != StatusReserva.RESERVADA.value:
            return False
        
        self.status = StatusReserva.APROVADA.value
        return True
    
    def despachar(self):
        """
        Despacha a reserva (move para status DESPACHADA).
        
        Returns:
            bool: True se o despacho foi bem-sucedido, False caso contrário
        """
        if self.status != StatusReserva.CONFIRMADA.value:
            return False
        
        self.status = StatusReserva.DESPACHADA.value
        return True
    
    def rejeitar(self, usuario_id, motivo=None):
        """
        Rejeita a reserva (move para status REJEITADA).
        
        Args:
            usuario_id: ID do usuário que rejeita (usuário da farmácia doadora)
            motivo: Motivo da rejeição (opcional)
            
        Returns:
            bool: True se a rejeição foi bem-sucedida, False caso contrário
        """
        if self.status != StatusReserva.RESERVADA.value:
            return False
        
        self.status = StatusReserva.REJEITADA.value
        self.confirmado_por_id = usuario_id
        self.confirmado_em = datetime.utcnow()
        if motivo:
            self.observacoes = motivo
        return True
    
    def cancelar(self):
        """
        Cancela a reserva (move para status CANCELADA).
        
        Returns:
            bool: True se o cancelamento foi bem-sucedido, False caso contrário
        """
        if self.status not in [StatusReserva.RESERVADA.value, StatusReserva.CONFIRMADA.value]:
            return False
        
        self.status = StatusReserva.CANCELADA.value
        return True
    
    def expirar(self):
        """
        Expira a reserva (move para status EXPIRADA).
        
        Returns:
            bool: True se a expiração foi bem-sucedida, False caso contrário
        """
        if self.status != StatusReserva.RESERVADA.value:
            return False
        
        self.status = StatusReserva.EXPIRADA.value
        return True
    
    def __repr__(self):
        return f"<ReservaOferta {self.id} - {self.quantidade_reservada} unidades>"
