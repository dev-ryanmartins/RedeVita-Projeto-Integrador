from app.database import db
from datetime import datetime


class Instituicao(db.Model):
    """Modelo para Instituições Receptoras."""
    __tablename__ = "instituicoes"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=True)
    endereco = db.Column(db.String(300), nullable=True)
    responsavel = db.Column(db.String(100), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Instituicao {self.nome}>"
