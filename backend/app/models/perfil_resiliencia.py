"""
Modelo de Perfil de Resiliência da Farmácia Parceira

Armazena informações operacionais declaradas pelas farmácias parceiras
para planejamento de contingência. Não comprovam condições de armazenamento
nem autorizam recebimento ou transferência de medicamentos.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
import enum

from app.database import db


class SituacaoEnergiaEnum(enum.Enum):
    """Situação declarada de energia de contingência."""
    DISPONIVEL = "disponivel"
    NAO_DISPONIVEL = "nao_disponivel"
    DESCONHECIDA = "desconhecida"


class SituacaoRefrigeracaoEnum(enum.Enum):
    """Situação declarada de refrigeração de apoio."""
    DISPONIVEL = "disponivel"
    NAO_DISPONIVEL = "nao_disponivel"
    DESCONHECIDA = "desconhecida"


class ApoioTemporarioEnum(enum.Enum):
    """Possibilidade declarada de receber apoio temporário."""
    SIM = "sim"
    NAO = "nao"
    DESCONHECIDA = "desconhecida"


class PlanoContingenciaEnum(enum.Enum):
    """Plano operacional de contingência."""
    EXISTENTE = "existente"
    INEXISTENTE = "inexistente"
    PRECISA_REVISAO = "precisa_revisao"
    DESCONHECIDO = "desconhecido"


class OrigemInformacaoEnum(enum.Enum):
    """Origem da informação."""
    DECLARADA = "declarada"
    VERIFICADA = "verificada"


class PerfilResilienciaFarmacia(db.Model):
    """
    Perfil de Resiliência da Farmácia Parceira.
    
    Armazena informações operacionais declaradas ou verificadas administrativamente
    para planejamento de contingência. Não comprovam condições de armazenamento
    nem autorizam recebimento ou transferência de medicamentos.
    """
    __tablename__ = "perfis_resiliencia_farmacia"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    farmacia_id = Column(Integer, ForeignKey('farmacias.id'), nullable=False, unique=True, comment="ID da farmácia (único por farmácia)")
    
    # Situação declarada de energia de contingência
    situacao_energia = Column(Enum(SituacaoEnergiaEnum), default=SituacaoEnergiaEnum.DESCONHECIDA, nullable=False, comment="Situação declarada de energia de contingência")
    
    # Situação declarada de refrigeração de apoio
    situacao_refrigeracao = Column(Enum(SituacaoRefrigeracaoEnum), default=SituacaoRefrigeracaoEnum.DESCONHECIDA, nullable=False, comment="Situação declarada de refrigeração de apoio")
    
    # Possibilidade declarada de receber apoio temporário
    apoio_temporario = Column(Enum(ApoioTemporarioEnum), default=ApoioTemporarioEnum.DESCONHECIDA, nullable=False, comment="Possibilidade declarada de receber apoio temporário")
    
    # Plano operacional de contingência
    plano_contingencia = Column(Enum(PlanoContingenciaEnum), default=PlanoContingenciaEnum.DESCONHECIDO, nullable=False, comment="Plano operacional de contingência")
    
    # Datas de verificação
    data_ultima_verificacao = Column(DateTime, nullable=True, comment="Data da última verificação do perfil")
    data_prevista_revisao = Column(DateTime, nullable=True, comment="Data prevista para nova revisão")
    
    # Origem e responsável
    origem_informacao = Column(Enum(OrigemInformacaoEnum), default=OrigemInformacaoEnum.DECLARADA, nullable=False, comment="Origem da informação (declarada pela farmácia ou verificada por Admin)")
    usuario_responsavel_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True, comment="ID do usuário responsável pelo registro")
    
    # Audit trail
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Data de criação do registro")
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="Data da última atualização")
    
    # Relacionamentos
    farmacia = relationship("Farmacia", foreign_keys=[farmacia_id], lazy=True)
    usuario_responsavel = relationship("Usuario", foreign_keys=[usuario_responsavel_id], lazy=True)

    def __repr__(self):
        return f"<PerfilResilienciaFarmacia Farmacia {self.farmacia_id}>"

    def to_dict(self):
        """Converte para dicionário para API responses."""
        return {
            'id': self.id,
            'farmacia_id': self.farmacia_id,
            'farmacia_nome': self.farmacia.nome_fantasia if self.farmacia else None,
            'situacao_energia': self.situacao_energia.value if self.situacao_energia else None,
            'situacao_refrigeracao': self.situacao_refrigeracao.value if self.situacao_refrigeracao else None,
            'apoio_temporario': self.apoio_temporario.value if self.apoio_temporario else None,
            'plano_contingencia': self.plano_contingencia.value if self.plano_contingencia else None,
            'data_ultima_verificacao': self.data_ultima_verificacao.isoformat() if self.data_ultima_verificacao else None,
            'data_prevista_revisao': self.data_prevista_revisao.isoformat() if self.data_prevista_revisao else None,
            'origem_informacao': self.origem_informacao.value if self.origem_informacao else None,
            'usuario_responsavel_id': self.usuario_responsavel_id,
            'usuario_responsavel_nome': self.usuario_responsavel.nome if self.usuario_responsavel else None,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }

    def esta_desatualizado(self, dias_limite=90):
        """
        Verifica se o perfil está desatualizado.
        
        Args:
            dias_limite: Número de dias considerados como limite para atualização
            
        Returns:
            True se estiver desatualizado, False caso contrário
        """
        if not self.data_ultima_verificacao:
            return True
        
        dias_desde_verificacao = (datetime.utcnow() - self.data_ultima_verificacao).days
        return dias_desde_verificacao > dias_limite
