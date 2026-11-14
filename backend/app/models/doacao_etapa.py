from app.database import db
from datetime import datetime
from enum import Enum


class TipoEtapa(Enum):
    """Tipos de etapas que podem ser registradas em uma doação."""
    REGISTRO_CRIADO = "registro_criado"
    PESAGEM_REGISTRADA = "pesagem_registrada"
    CONFERENCIA_MANUAL_REQUERIDA = "conferencia_manual_requerida"
    CONFERENCIA_MANUAL_CONCLUIDA = "conferencia_manual_concluida"
    CANCELAMENTO = "cancelamento"
    COMPENSACAO = "compensacao"


class OrigemEvento(Enum):
    """Origem do evento: sistema ou ação manual do usuário."""
    SISTEMA = "sistema"
    USUARIO = "usuario"


class DoacaoEtapa(db.Model):
    """Registro auditável de etapas de uma doação."""
    __tablename__ = "doacoes_etapas"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    doacao_id = db.Column(db.Integer, db.ForeignKey("doacoes.id"), nullable=False, index=True)
    tipo_etapa = db.Column(db.String(50), nullable=False, comment="Tipo da etapa (enum TipoEtapa)")
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment="Data/hora do evento em UTC")
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True, comment="Usuário responsável (null para eventos automáticos)")
    origem = db.Column(db.String(20), nullable=False, default=OrigemEvento.SISTEMA.value, comment="Origem do evento (enum OrigemEvento)")
    observacao = db.Column(db.Text, nullable=True, comment="Observação opcional sobre a etapa")

    # Campos de auditoria
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relacionamentos
    doacao = db.relationship("Doacao", backref="etapas")
    usuario = db.relationship("Usuario", backref="etapas_registradas")

    def to_dict(self):
        """Converte para dicionário para serialização."""
        return {
            "id": self.id,
            "doacao_id": self.doacao_id,
            "tipo_etapa": self.tipo_etapa,
            "data_hora": self.data_hora.isoformat() if self.data_hora else None,
            "usuario_id": self.usuario_id,
            "usuario_nome": self.usuario.nome if self.usuario else None,
            "origem": self.origem,
            "observacao": self.observacao,
            "criado_em": self.criado_em.isoformat() if self.criado_em else None,
        }
