"""
IoT Models - Modelos de Dados para Telemetria e RFID
Conforme normas ANVISA RDC 44/2009 e RDC 430/2020 para cadeia de frio e rastreabilidade
Disciplina: ADS - Módulo 4 - Internet das Coisas e Hardware Virtual
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
import enum
import uuid

from app.database import db


class StatusAlertaEnum(enum.Enum):
    """Enum para status de alerta térmico conforme ANVISA"""
    NORMAL = "NORMAL"
    ALERTA_LEVE = "ALERTA_LEVE"
    CRITICO_TERMICO = "CRITICO_TERMICO"


class ResultadoLoteEnum(enum.Enum):
    """Enum para resultado do processamento de lote"""
    COMPLETO = "COMPLETO"
    PARCIAL = "PARCIAL"
    REJEITADO = "REJEITADO"


class LoteTelemetria(db.Model):
    """
    Tabela de histórico de lotes de telemetria recebidos pela API.
    Armazena metadados operacionais para diagnóstico de sincronização IoT.
    
    NOTA: Esta tabela não armazena payloads completos, dados de pacientes,
    credenciais ou mensagens de exceção. Apenas metadados operacionais.
    
    NOTA: O endpoint /iot/telemetria/lote não tem autenticação confiável.
    Os identificadores de dispositivo são declarados no payload e não
    comprovam identidade ou execução única.
    """
    __tablename__ = 'lotes_telemetria'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    lote_id = Column(String(36), unique=True, nullable=False, index=True, comment="UUID interno gerado no servidor")
    data_recebimento = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, comment="Timestamp de recebimento no servidor (UTC)")
    total_recebidas = Column(Integer, nullable=False, comment="Total de leituras recebidas no lote")
    total_processadas = Column(Integer, nullable=False, comment="Total de leituras processadas com sucesso")
    total_rejeitadas = Column(Integer, nullable=False, comment="Total de leituras rejeitadas")
    resultado = Column(Enum(ResultadoLoteEnum), nullable=False, comment="Resultado agregado do processamento")
    qtd_dispositivos = Column(Integer, nullable=False, comment="Quantidade de dispositivos distintos no lote")
    dispositivo_principal = Column(String(50), nullable=True, comment="ID do dispositivo quando há apenas um no lote (não autenticado)")
    erros_por_categoria = Column(JSON, nullable=True, comment="Categorias e quantidades de erros, sem mensagens brutas")

    def __repr__(self):
        return f"<LoteTelemetria {self.lote_id} - {self.resultado.value}>"

    def to_dict(self):
        """Converte para dicionário para API responses"""
        return {
            'id': self.id,
            'lote_id': self.lote_id,
            'data_recebimento': self.data_recebimento.isoformat() if self.data_recebimento else None,
            'total_recebidas': self.total_recebidas,
            'total_processadas': self.total_processadas,
            'total_rejeitadas': self.total_rejeitadas,
            'resultado': self.resultado.value,
            'qtd_dispositivos': self.qtd_dispositivos,
            'dispositivo_principal': self.dispositivo_principal,
            'erros_por_categoria': self.erros_por_categoria
        }


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
