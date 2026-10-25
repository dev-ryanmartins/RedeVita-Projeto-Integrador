from app.database import db
from datetime import datetime


class MovimentoEstoque(db.Model):
    """
    Modelo para movimentos de estoque (ledger).
    
    Registra todas as entradas e saídas de estoque para rastreabilidade.
    """
    __tablename__ = "movimentos_estoque"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    
    # Medicamento e quantidade
    medicamento_id = db.Column(db.Integer, db.ForeignKey("medicamentos.id"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    
    # Tipo de movimento
    tipo = db.Column(db.String(50), nullable=False)
    # Tipos: entrada, saida, ajuste_adicao, ajuste_subtracao
    
    # Idempotência
    operacao_id = db.Column(db.String(64), unique=True, nullable=True, index=True)
    
    # Responsáveis
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    autorizado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Contexto
    justificativa = db.Column(db.Text, nullable=True)
    referencia_documento = db.Column(db.String(100), nullable=True)
    
    # Relacionamentos
    medicamento = db.relationship("Medicamento", overlaps='medicamento', backref="movimentos")
    usuario = db.relationship("Usuario", foreign_keys=[usuario_id], overlaps='usuario', backref="movimentos")
    autorizado_por = db.relationship("Usuario", foreign_keys=[autorizado_por_id], overlaps='usuario')
    
    @staticmethod
    def gerar_operacao_id():
        """Gera um ID de operação único."""
        import secrets
        return secrets.token_urlsafe(48)
