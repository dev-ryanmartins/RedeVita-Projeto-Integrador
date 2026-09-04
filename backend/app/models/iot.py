"""
IoT Models - Modelos de Dados para Telemetria e RFID
Conforme normas ANVISA RDC 44/2009 e RDC 430/2020 para cadeia de frio e rastreabilidade
Disciplina: ADS - Módulo 4 - Internet das Coisas e Hardware Virtual
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
import enum

from app.database import db


class StatusAlertaEnum(enum.Enum):
    """Enum para status de alerta térmico conforme ANVISA"""
    NORMAL = "NORMAL"
    ALERTA_LEVE = "ALERTA_LEVE"
    CRITICO_TERMICO = "CRITICO_TERMICO"


class LeituraIoT(db.Model):
    """
    Tabela de leituras de telemetria IoT (temperatura/umidade).
    Monitoramento de cadeia de frio conforme normas ANVISA.
    
    REGRA DE NEGÓCIO: Toda leitura IoT deve estar vinculada a uma farmácia
    parceira cadastrada no sistema para garantir rastreabilidade e
    conformidade com Portaria 344/ANVISA.
    """
    __tablename__ = 'leituras_iot'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    dispositivo_id = Column(String(50), nullable=False, index=True, comment="ID único do dispositivo ESP32/sensor")
    farmacia_id = Column(Integer, ForeignKey('farmacias.id'), nullable=False, comment="ID da farmácia associada (OBRIGATÓRIO)")
    temperatura = Column(Float, nullable=False, comment="Temperatura em °C")
    umidade = Column(Float, nullable=False, comment="Umidade relativa em %")
    luminosidade_lux = Column(Float, nullable=True, comment="Luminosidade em lux (fotodegradação)")
    status_alerta = Column(Enum(StatusAlertaEnum), default=StatusAlertaEnum.NORMAL, nullable=False, comment="Status conforme regras ANVISA")
    data_hora = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="Timestamp da leitura")
    farmacia = relationship("Farmacia", foreign_keys=[farmacia_id], lazy=True)

    def __init__(self, **kwargs):
        status_provided = "status_alerta" in kwargs
        super().__init__(**kwargs)
        if not status_provided and self.temperatura is not None and self.umidade is not None:
            if 15.0 <= self.temperatura <= 25.0 and self.umidade <= 70.0:
                self.status_alerta = StatusAlertaEnum.NORMAL
            elif (
                10.0 <= self.temperatura < 15.0
                or 25.0 < self.temperatura <= 30.0
                or (15.0 <= self.temperatura <= 25.0 and self.umidade > 70.0)
            ):
                self.status_alerta = StatusAlertaEnum.ALERTA_LEVE
            else:
                self.status_alerta = StatusAlertaEnum.CRITICO_TERMICO

    def __repr__(self):
        return f"<LeituraIoT {self.dispositivo_id} - {self.temperatura}°C - {self.status_alerta.value}>"

    def to_dict(self):
        """Converte para dicionário para API responses"""
        return {
            'id': self.id,
            'dispositivo_id': self.dispositivo_id,
            'farmacia_id': self.farmacia_id,
            'temperatura': self.temperatura,
            'umidade': self.umidade,
            'luminosidade_lux': self.luminosidade_lux,
            'status_alerta': self.status_alerta.value,
            'data_hora': self.data_hora.isoformat() if self.data_hora else None
        }


class TagRFID(db.Model):
    """
    Tabela de tags RFID/NFC para controle de acesso físico.
    Armazena hash SHA-256 da tag física para segurança.
    """
    __tablename__ = 'tags_rfid'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    tag_uid = Column(String(64), unique=True, nullable=False, index=True, comment="Hash SHA-256 da tag física")
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False, comment="ID do usuário associado")
    descricao = Column(String(100), nullable=True, comment="Descrição da tag (ex: Crachá Farmacêutico)")
    ativo = Column(Boolean, default=True, nullable=False, comment="Se a tag está ativa para uso")
    data_cadastro = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Data de cadastro da tag")
    ultimo_acesso = Column(DateTime, nullable=True, comment="Último acesso autorizado")
    usuario = relationship("Usuario", foreign_keys=[usuario_id], lazy=True)

    def __repr__(self):
        return f"<TagRFID {self.tag_uid[:16]}... - Usuário {self.usuario_id}>"

    def to_dict(self):
        """Converte para dicionário para API responses"""
        return {
            'id': self.id,
            'tag_uid': self.tag_uid,
            'usuario_id': self.usuario_id,
            'descricao': self.descricao,
            'ativo': self.ativo,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None,
            'ultimo_acesso': self.ultimo_acesso.isoformat() if self.ultimo_acesso else None
        }


# Índices compostos para otimização de consultas
Index('idx_leituras_dispositivo_data', LeituraIoT.dispositivo_id, LeituraIoT.data_hora)
Index('idx_leituras_farmacia_data', LeituraIoT.farmacia_id, LeituraIoT.data_hora)
