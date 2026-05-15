from app.database import db
from datetime import datetime


class Receita(db.Model):
    __tablename__ = 'receitas'

    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey('medicos.id'), nullable=False)
    medicamento_id = db.Column(db.Integer, db.ForeignKey('medicamentos.id'), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    data_emissao = db.Column(db.DateTime, default=datetime.utcnow)

    tipo_receita = db.Column(db.String(60), nullable=True)

    imagem_url = db.Column(db.String(255), nullable=True)

    status = db.Column(db.String(20), default='pendente', nullable=False)
    dispensada_em = db.Column(db.DateTime, nullable=True)
    dispensada_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    paciente = db.relationship('Paciente', backref='receitas', lazy=True)
    medico = db.relationship('Medico', backref='receitas', lazy=True)
    medicamento = db.relationship('Medicamento', backref='receitas', lazy=True)
    dispensada_por = db.relationship('Usuario', foreign_keys=[dispensada_por_id], lazy=True)

    def __repr__(self):
        return f'<Receita {self.id} - Paciente {self.paciente_id} - {self.status}>'
