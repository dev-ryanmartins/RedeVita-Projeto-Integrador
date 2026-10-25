from app.database import db
from datetime import datetime


class ContagemEstoque(db.Model):
    """Modelo para contagem cíclica de estoque."""
    __tablename__ = "contagens_estoque"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    medicamento_id = db.Column(db.Integer, db.ForeignKey("medicamentos.id"), nullable=False)
    lote = db.Column(db.String(50), nullable=False)
    quantidade_fisica = db.Column(db.Integer, nullable=False)
    quantidade_sistema = db.Column(db.Integer, nullable=False)
    divergencia = db.Column(db.Integer, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    autorizado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    finalizada_em = db.Column(db.DateTime, nullable=True)
    estado = db.Column(db.String(20), default="EM_ANDAMENTO", nullable=False)
    ajuste_realizado = db.Column(db.Boolean, default=False, nullable=False)
    ajuste_realizado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    ajuste_realizado_em = db.Column(db.DateTime, nullable=True)
    justificativa_ajuste = db.Column(db.Text, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
