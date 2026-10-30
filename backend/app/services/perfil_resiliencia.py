"""
Serviço de Perfil de Resiliência da Farmácia Parceira

NOTA: Esta funcionalidade depende da tabela perfis_resiliencia_farmacia,
que requer migration não implementada devido a bloqueio no ambiente atual.
Este serviço retorna dados de demonstração para fins de validação.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.models.farmacia import Farmacia


class PerfilResilienciaService:
    """Serviço de perfil de resiliência."""

    def __init__(self):
        """Inicializa o serviço."""
        pass

    def obter_todos_perfis(self) -> List[Dict[str, Any]]:
        """
        Obtém todos os perfis de resiliência.
        
        Returns:
            Lista de perfis (dados de demonstração)
        """
        # Dados de demonstração - substituir por consulta real quando migration estiver implementada
        farmacias = Farmacia.query.all()
        perfis = []
        
        for farmacia in farmacias:
            perfil = {
                'id': farmacia.id,
                'farmacia_id': farmacia.id,
                'farmacia_nome': farmacia.nome_fantasia,
                'situacao_energia': 'desconhecida',
                'situacao_refrigeracao': 'desconhecida',
                'apoio_temporario': 'desconhecida',
                'plano_contingencia': 'desconhecido',
                'data_ultima_verificacao': None,
                'data_prevista_revisao': None,
                'origem_informacao': 'declarada',
                'usuario_responsavel_id': None,
                'usuario_responsavel_nome': None,
                'criado_em': datetime.utcnow().isoformat(),
                'atualizado_em': datetime.utcnow().isoformat(),
                'desatualizado': True
            }
            perfis.append(perfil)
        
        return perfis

    def obter_perfil_por_farmacia(self, farmacia_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém o perfil de resiliência de uma farmácia específica.
        
        Args:
            farmacia_id: ID da farmácia
            
        Returns:
            Perfil da farmácia ou None
        """
        farmacia = Farmacia.query.get(farmacia_id)
        if not farmacia:
            return None
        
        # Dados de demonstração
        return {
            'id': farmacia.id,
            'farmacia_id': farmacia.id,
            'farmacia_nome': farmacia.nome_fantasia,
            'situacao_energia': 'desconhecida',
            'situacao_refrigeracao': 'desconhecida',
            'apoio_temporario': 'desconhecida',
            'plano_contingencia': 'desconhecido',
            'data_ultima_verificacao': None,
            'data_prevista_revisao': None,
            'origem_informacao': 'declarada',
            'usuario_responsavel_id': None,
            'usuario_responsavel_nome': None,
            'criado_em': datetime.utcnow().isoformat(),
            'atualizado_em': datetime.utcnow().isoformat(),
            'desatualizado': True
        }

    def criar_perfil(self, farmacia_id: int, dados: Dict[str, Any], usuario_id: int) -> Dict[str, Any]:
        """
        Cria um novo perfil de resiliência.
        
        Args:
            farmacia_id: ID da farmácia
            dados: Dados do perfil
            usuario_id: ID do usuário responsável
            
        Returns:
            Perfil criado (dados de demonstração)
        """
        farmacia = Farmacia.query.get(farmacia_id)
        if not farmacia:
            raise ValueError("Farmácia não encontrada")
        
        # Dados de demonstração - não persiste
        return {
            'id': farmacia.id,
            'farmacia_id': farmacia_id,
            'farmacia_nome': farmacia.nome_fantasia,
            'situacao_energia': dados.get('situacao_energia', 'desconhecida'),
            'situacao_refrigeracao': dados.get('situacao_refrigeracao', 'desconhecida'),
            'apoio_temporario': dados.get('apoio_temporario', 'desconhecida'),
            'plano_contingencia': dados.get('plano_contingencia', 'desconhecido'),
            'data_ultima_verificacao': dados.get('data_ultima_verificacao'),
            'data_prevista_revisao': dados.get('data_prevista_revisao'),
            'origem_informacao': dados.get('origem_informacao', 'declarada'),
            'usuario_responsavel_id': usuario_id,
            'usuario_responsavel_nome': None,
            'criado_em': datetime.utcnow().isoformat(),
            'atualizado_em': datetime.utcnow().isoformat(),
            'desatualizado': False
        }

    def atualizar_perfil(self, farmacia_id: int, dados: Dict[str, Any], usuario_id: int) -> Dict[str, Any]:
        """
        Atualiza um perfil de resiliência existente.
        
        Args:
            farmacia_id: ID da farmácia
            dados: Dados do perfil
            usuario_id: ID do usuário responsável
            
        Returns:
            Perfil atualizado (dados de demonstração)
        """
        farmacia = Farmacia.query.get(farmacia_id)
        if not farmacia:
            raise ValueError("Farmácia não encontrada")
        
        # Dados de demonstração - não persiste
        return {
            'id': farmacia.id,
            'farmacia_id': farmacia_id,
            'farmacia_nome': farmacia.nome_fantasia,
            'situacao_energia': dados.get('situacao_energia', 'desconhecida'),
            'situacao_refrigeracao': dados.get('situacao_refrigeracao', 'desconhecida'),
            'apoio_temporario': dados.get('apoio_temporario', 'desconhecida'),
            'plano_contingencia': dados.get('plano_contingencia', 'desconhecido'),
            'data_ultima_verificacao': dados.get('data_ultima_verificacao'),
            'data_prevista_revisao': dados.get('data_prevista_revisao'),
            'origem_informacao': dados.get('origem_informacao', 'verificada'),
            'usuario_responsavel_id': usuario_id,
            'usuario_responsavel_nome': None,
            'criado_em': datetime.utcnow().isoformat(),
            'atualizado_em': datetime.utcnow().isoformat(),
            'desatualizado': False
        }

    def obter_ultima_leitura_iot(self, farmacia_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém a última leitura IoT de uma farmácia.
        
        Args:
            farmacia_id: ID da farmácia
            
        Returns:
            Informações da última leitura ou None
        """
        from app.models.iot import LeituraIoT
        
        leitura = LeituraIoT.query.filter_by(farmacia_id=farmacia_id).order_by(LeituraIoT.data_hora.desc()).first()
        
        if not leitura:
            return None
        
        return {
            'data_hora': leitura.data_hora.isoformat() if leitura.data_hora else None,
            'temperatura': leitura.temperatura,
            'umidade': leitura.umidade,
            'status_alerta': leitura.status_alerta.value if leitura.status_alerta else None,
            'dispositivo_id': leitura.dispositivo_id
        }
