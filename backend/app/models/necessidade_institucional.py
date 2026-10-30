"""
Modelo para Necessidade Institucional

NOTA: Esta funcionalidade é Admin-only devido à ausência de vínculo confiável
entre usuários e instituições/farmácias no modelo atual.
"""

from app.database import db
from datetime import datetime
from enum import Enum


class StatusNecessidade(Enum):
    """Status operacional da necessidade."""
    RASCUNHO = "rascunho"
    EM_REVISAO = "em_revisao"
    REGISTRADA = "registrada"
    ENCERRADA = "encerrada"


class PrioridadeNecessidade(Enum):
    """Prioridade declarada pela instituição."""
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"


class NecessidadeInstitucional(db.Model):
    """Modelo para necessidades agregadas de instituições."""
    __tablename__ = "necessidades_institucionais"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    
    # Instituição (nome informado, pois não há vínculo confiável com Farmacia)
    nome_instituicao = db.Column(db.String(200), nullable=False)
    
    # Produto (referência opcional para catálogo existente)
    medicamento_referencia_id = db.Column(
        db.Integer, 
        db.ForeignKey("medicamentos_referencia.id"), 
        nullable=True
    )
    
    # Se não houver referência, permite nome descritivo
    produto_descritivo = db.Column(db.String(200), nullable=True)
    
    quantidade_solicitada = db.Column(db.Integer, nullable=False)
    unidade = db.Column(db.String(20), nullable=False, default="unidade")
    
    data_desejada = db.Column(db.Date, nullable=True)
    
    prioridade = db.Column(db.String(20), nullable=False, default=PrioridadeNecessidade.MEDIA.value)
    
    status = db.Column(db.String(20), nullable=False, default=StatusNecessidade.RASCUNHO.value)
    
    # Campos de auditoria
    criado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    revisado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    revisado_em = db.Column(db.DateTime, nullable=True)
    
    encerrado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    encerrado_em = db.Column(db.DateTime, nullable=True)
    
    observacoes = db.Column(db.Text, nullable=True)
    
    # Relacionamentos
    criado_por = db.relationship("Usuario", foreign_keys=[criado_por_id], overlaps='usuario')
    revisado_por = db.relationship("Usuario", foreign_keys=[revisado_por_id], overlaps='usuario')
    encerrado_por = db.relationship("Usuario", foreign_keys=[encerrado_por_id], overlaps='usuario')
    referencia = db.relationship("MedicamentoReferencia", backref="necessidades", lazy=True)
    
    def __repr__(self):
        return f"<NecessidadeInstitucional {self.nome_instituicao} - {self.produto_descritivo or 'N/A'}>"
