"""
Modelo para Agendamento de Entrega entre Participantes Autorizados

NOTA: Esta funcionalidade é Admin-only devido à ausência de vínculo confiável
entre usuários e farmácias no modelo atual.
"""

from app.database import db
from datetime import datetime
from enum import Enum


class EstadoAgendamento(Enum):
    """Estado do agendamento."""
    PROPOSTA = "proposta"
    AGUARDANDO_ORIGEM = "aguardando_confirmacao_origem"
    AGUARDANDO_DESTINO = "aguardando_confirmacao_destino"
    CONFIRMADO = "confirmado"
    CANCELADO = "cancelado"
    ENCERRADO_SEM_CONFIRMACAO = "encerrado_sem_confirmacao"


class AgendamentoEntrega(db.Model):
    """Modelo para agendamentos de entrega entre farmácias."""
    __tablename__ = "agendamentos_entrega"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    
    # Participantes
    farmacia_origem_id = db.Column(db.Integer, db.ForeignKey("farmacias.id"), nullable=False)
    farmacia_destino_id = db.Column(db.Integer, db.ForeignKey("farmacias.id"), nullable=False)
    
    # Intervalo proposto
    data_hora_inicio = db.Column(db.DateTime, nullable=False)
    data_hora_fim = db.Column(db.DateTime, nullable=False)
    
    # Estado
    estado = db.Column(db.String(50), nullable=False, default=EstadoAgendamento.PROPOSTA.value)
    
    # Auditoria
    criado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    confirmado_origem_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    confirmado_origem_em = db.Column(db.DateTime, nullable=True)
    
    confirmado_destino_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    confirmado_destino_em = db.Column(db.DateTime, nullable=True)
    
    cancelado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    cancelado_em = db.Column(db.DateTime, nullable=True)
    motivo_cancelamento = db.Column(db.Text, nullable=True)
    
    observacoes = db.Column(db.Text, nullable=True)
    
    # Relacionamentos
    farmacia_origem = db.relationship("Farmacia", foreign_keys=[farmacia_origem_id], overlaps='farmacia')
    farmacia_destino = db.relationship("Farmacia", foreign_keys=[farmacia_destino_id], overlaps='farmacia')
    criado_por = db.relationship("Usuario", foreign_keys=[criado_por_id], overlaps='usuario')
    confirmado_origem_por = db.relationship("Usuario", foreign_keys=[confirmado_origem_por_id], overlaps='usuario')
    confirmado_destino_por = db.relationship("Usuario", foreign_keys=[confirmado_destino_por_id], overlaps='usuario')
    cancelado_por = db.relationship("Usuario", foreign_keys=[cancelado_por_id], overlaps='usuario')
    
    def __repr__(self):
        return f"<AgendamentoEntrega {self.farmacia_origem.nome_fantasia} -> {self.farmacia_destino.nome_fantasia}>"
