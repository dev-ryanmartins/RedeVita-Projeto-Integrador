from app.database import db
from datetime import datetime


class Doacao(db.Model):
    __tablename__ = "doacoes"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    medicamento_id = db.Column(
        db.Integer, db.ForeignKey("medicamentos.id"), nullable=False
    )
    data_doacao = db.Column(db.DateTime, default=datetime.utcnow)
    quantidade = db.Column(db.Integer, nullable=False)
    peso_gramas = db.Column(db.Float, nullable=True, comment="Peso em gramas da doação (referência)")
    status_conferencia = db.Column(db.String(50), default="APROVADO", comment="Status da conferência: APROVADO, PENDENTE_CONFERENCIA_MANUAL")
    
    # Campos para compensação/cancelação (append-only ledger)
    cancelado = db.Column(db.Boolean, default=False, nullable=False)
    cancelado_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    cancelado_em = db.Column(db.DateTime, nullable=True)
    justificativa_cancelamento = db.Column(db.Text, nullable=True)
    compensacao_id = db.Column(db.Integer, db.ForeignKey("doacoes.id"), nullable=True)

    # Relacionamentos para facilitar a consulta
    usuario = db.relationship("Usuario", foreign_keys=[usuario_id], overlaps='usuario', backref="doacoes")
    medicamento = db.relationship("Medicamento", overlaps='medicamento', backref="registros_doacao")
    cancelado_por = db.relationship("Usuario", foreign_keys=[cancelado_por_id], overlaps='usuario')
    compensacao = db.relationship("Doacao", remote_side=[id], foreign_keys=[compensacao_id])
