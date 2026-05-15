from app.database import db
from datetime import datetime


class Medico(db.Model):
    __tablename__ = 'medicos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    crm = db.Column(db.String(30), nullable=False, unique=True)
    especialidade = db.Column(db.String(100), nullable=False)
    contato = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Medico {self.nome}>'
