from app.database import db
from datetime import datetime


class Campanha(db.Model):
    __tablename__ = "campanhas"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # arrecadacao, alerta, informativo
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='ativa')  # ativa, concluida, cancelada
    criador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Campanha {self.titulo}>"
