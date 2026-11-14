from app.database import db
from datetime import datetime


class SolicitacaoEstoque(db.Model):
    """Modelo para solicitações de estoque."""
    __tablename__ = "solicitacoes_estoque"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    medicamento_id = db.Column(db.Integer, db.ForeignKey("medicamentos.id"), nullable=False)
    lote = db.Column(db.String(50), nullable=False)
    quantidade_solicitada = db.Column(db.Integer, nullable=False)
    quantidade_reservada = db.Column(db.Integer, nullable=True)
    quantidade_retirada = db.Column(db.Integer, nullable=True)
    estado = db.Column(db.String(50), default="PENDENTE", nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    aprovado_em = db.Column(db.DateTime, nullable=True)
    reservado_em = db.Column(db.DateTime, nullable=True)
    retirado_em = db.Column(db.DateTime, nullable=True)
    cancelado_em = db.Column(db.DateTime, nullable=True)
    expira_em = db.Column(db.DateTime, nullable=True)
    aprovado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    reservado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    retirado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    cancelado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    justificativa = db.Column(db.Text, nullable=True)
    justificativa_cancelamento = db.Column(db.Text, nullable=True)
