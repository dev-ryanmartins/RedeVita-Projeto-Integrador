from app.database import db
from flask_login import UserMixin


class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    senha = db.Column(db.String(255), nullable=False)
    cargo = db.Column(db.String(50), default='Voluntário')
    ativo = db.Column(db.Boolean, default=True, nullable=True)

    def __repr__(self):
        return f'<Usuario {self.nome}>'

    def is_admin(self):
        return self.cargo == 'Admin'

    def is_active(self):
        return self.ativo is not False
