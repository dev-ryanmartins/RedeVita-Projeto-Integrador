from app.database import db
from datetime import datetime

class Doacao(db.Model):
    __tablename__ = 'doacoes'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    medicamento_id = db.Column(db.Integer, db.ForeignKey('medicamentos.id'), nullable=False)
    data_doacao = db.Column(db.DateTime, default=datetime.utcnow)
    quantidade = db.Column(db.Integer, nullable=False)

    # Relacionamentos para facilitar a consulta
    usuario = db.relationship('Usuario', backref='minhas_doacoes')
    medicamento = db.relationship('Medicamento', backref='registros_doacao')