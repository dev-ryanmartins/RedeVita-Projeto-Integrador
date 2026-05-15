from app.database import db
from datetime import datetime


class Medicamento(db.Model):
    __tablename__ = 'medicamentos'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    lote = db.Column(db.String(50), nullable=False)
    data_validade = db.Column(db.Date, nullable=False)
    quantidade = db.Column(db.Integer, default=0)

    # Status semáforo: 0=Verde (Ok), 1=Amarelo (Atenção), 2=Vermelho (Vencido)
    status_semaforo = db.Column(db.Integer, default=0)

    # Campos ANVISA
    tarja = db.Column(db.String(30), default='Sem Tarja', nullable=False)
    principio_ativo = db.Column(db.String(120), nullable=True)
    uso_continuo = db.Column(db.Boolean, default=False)
    referencia_id = db.Column(db.Integer, db.ForeignKey('medicamentos_referencia.id'), nullable=True)

    referencia = db.relationship('MedicamentoReferencia', backref='medicamentos', lazy=True)

    @property
    def controlado(self):
        return self.tarja == 'Portaria 344'

    @property
    def tipo_receita_requerida(self):
        mapa = {
            'Portaria 344': "Receita 'B' Especial (Azul) ou 'A' (Amarela)",
            'Tarja Vermelha': 'Receita de Controle Especial (Branca)',
            'Tarja Amarela': 'Receita Simples',
            'Sem Tarja': 'Isento de Prescrição',
        }
        return mapa.get(self.tarja, 'Receita Simples')

    def __repr__(self):
        return f'<Medicamento {self.nome}>'
