from app.database import db


class MedicamentoReferencia(db.Model):
    __tablename__ = "medicamentos_referencia"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    nome_comercial = db.Column(db.String(120), nullable=False)
    registro_ms = db.Column(db.String(30), nullable=True)
    principio_ativo = db.Column(db.String(120), nullable=True)
    tarja = db.Column(db.String(30), default="Sem Tarja", nullable=False)
    uso_continuo = db.Column(db.Boolean, default=False)
    tipo_receita = db.Column(db.String(60), nullable=True)
    lista_portaria = db.Column(db.String(10), nullable=True)

    def __repr__(self):
        return f"<MedicamentoReferencia {self.nome_comercial}>"

    def to_dict(self):
        return {
            "id": self.id,
            "nome_comercial": self.nome_comercial,
            "registro_ms": self.registro_ms or "",
            "principio_ativo": self.principio_ativo or "",
            "tarja": self.tarja,
            "uso_continuo": self.uso_continuo,
            "tipo_receita": self.tipo_receita or "",
            "lista_portaria": self.lista_portaria or "",
        }
