import unicodedata
from app.database import db
from sqlalchemy import event


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(normalized.lower().split())


class Medicamento(db.Model):
    __tablename__ = "medicamentos"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    lote = db.Column(db.String(50), nullable=False)
    data_validade = db.Column(db.Date, nullable=False)
    quantidade = db.Column(db.Integer, default=0)

    # Status semáforo: 0=Verde (Ok), 1=Amarelo (Atenção), 2=Vermelho (Vencido)
    status_semaforo = db.Column(db.Integer, default=0)

    # Campos ANVISA
    tarja = db.Column(db.String(30), default="Sem Tarja", nullable=False)
    principio_ativo = db.Column(db.String(120), nullable=True)
    uso_continuo = db.Column(db.Boolean, default=False)
    referencia_id = db.Column(
        db.Integer, db.ForeignKey("medicamentos_referencia.id"), nullable=True
    )

    referencia = db.relationship(
        "MedicamentoReferencia", backref="medicamentos", lazy=True
    )

    @property
    def controlado(self):
        return self.tarja == "Portaria 344"

    @property
    def tipo_receita_requerida(self):
        mapa = {
            "Portaria 344": "Receita 'B' Especial (Azul) ou 'A' (Amarela)",
            "Tarja Vermelha": "Receita de Controle Especial (Branca)",
            "Tarja Amarela": "Receita Simples",
            "Sem Tarja": "Isento de Prescrição",
        }
        return mapa.get(self.tarja, "Receita Simples")

    def validar_portaria_344(self):
        """
        Valida se o medicamento está em conformidade com a Portaria 344/ANVISA.
        Se o principio_ativo ou referencia indicarem substância controlada,
        a tarja deve ser 'Portaria 344'.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        from app.models.medicamento_referencia import MedicamentoReferencia
        
        # Verifica se há referência vinculada
        if self.referencia_id:
            referencia = MedicamentoReferencia.query.get(self.referencia_id)
            if referencia and referencia.lista_portaria:
                # Substância está na lista da Portaria 344
                if self.tarja != "Portaria 344":
                    return False, f"Substância controlada (Lista {referencia.lista_portaria}): tarja deve ser 'Portaria 344'"
        
        # Verifica pelo principio_ativo se não houver referência
        if self.principio_ativo and not self.referencia_id:
            normalized_pa = _normalize_text(self.principio_ativo)
            if normalized_pa:
                referencias = MedicamentoReferencia.query.filter(
                    MedicamentoReferencia.principio_ativo.isnot(None)
                ).all()
                for referencia in referencias:
                    if _normalize_text(referencia.principio_ativo) == normalized_pa:
                        if referencia.lista_portaria and self.tarja != "Portaria 344":
                            return False, f"Princípio ativo controlado (Lista {referencia.lista_portaria}): tarja deve ser 'Portaria 344'"
                        break
        
        return True, None

    def __repr__(self):
        return f"<Medicamento {self.nome}>"


def _validar_portaria_344_medicamento(mapper, connection, target):
    is_valid, error_msg = target.validar_portaria_344()
    if not is_valid:
        raise ValueError(error_msg)


event.listen(Medicamento, "before_insert", _validar_portaria_344_medicamento)
event.listen(Medicamento, "before_update", _validar_portaria_344_medicamento)
