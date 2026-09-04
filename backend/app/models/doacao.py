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

    # Relacionamentos para facilitar a consulta
    usuario = db.relationship("Usuario", overlaps='usuario', backref="doacoes")
    medicamento = db.relationship("Medicamento", overlaps='medicamento', backref="registros_doacao")
