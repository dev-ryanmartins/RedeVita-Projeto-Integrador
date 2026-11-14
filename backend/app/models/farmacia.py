from app.database import db
from datetime import datetime


class Farmacia(db.Model):
    __tablename__ = "farmacias"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    nome_fantasia = db.Column(db.String(150), nullable=False)
    razao_social = db.Column(db.String(200), nullable=True)
    cnpj = db.Column(db.String(20), nullable=False, unique=True)
    endereco = db.Column(db.String(255), nullable=False)
    responsavel = db.Column(db.String(150), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Farmacia {self.nome_fantasia}>"
