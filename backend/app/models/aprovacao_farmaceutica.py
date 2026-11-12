from app.database import db
from datetime import datetime
from enum import Enum


class StatusAprovacao(Enum):
    """Status da aprovação farmacêutica."""
    APROVADA = "aprovada"
    REJEITADA = "rejeitada"


class AprovacaoFarmaceutica(db.Model):
    """
    Modelo para Aprovação Farmacêutica de Reservas.
    
    Registra a aprovação ou rejeição de uma reserva por um farmacêutico vinculado à farmácia de origem.
    """
    __tablename__ = "aprovacoes_farmaceuticas"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    
    # Reserva sendo aprovada/rejeitada
    reserva_id = db.Column(db.Integer, db.ForeignKey("reservas_ofertas.id"), nullable=False, unique=True)
    
    # Farmacêutico que aprovou/rejeitou
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    
    # Status da aprovação
    status = db.Column(db.String(20), nullable=False)
    
    # Observações (motivo da rejeição, notas da aprovação)
    observacoes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Idempotência
    operacao_id = db.Column(db.String(64), unique=True, nullable=True, index=True)
    
    # Relacionamentos
    reserva = db.relationship("ReservaOferta", foreign_keys=[reserva_id], lazy=True)
    usuario = db.relationship("Usuario", foreign_keys=[usuario_id], overlaps='usuario')
    
    def __repr__(self):
        return f"<AprovacaoFarmaceutica {self.id} - {self.status}>"
