from app.database import db
from datetime import datetime


class LogAtividade(db.Model):
    __tablename__ = "logs_atividade"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    acao = db.Column(db.String(100), nullable=False)
    detalhes = db.Column(db.String(500), nullable=True)
    ip = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship("Usuario", overlaps='usuario', backref="logs", lazy=True)

    def __repr__(self):
        return f"<Log {self.acao} em {self.created_at}>"
