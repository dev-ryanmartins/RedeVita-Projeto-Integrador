"""
Integração com a API da ANVISA para validação de medicamentos e registros sanitários
Conforme RDC 430/2020 - Consulta de regularidade de medicamentos

IMPORTANTE - BLOQUEIO DE CONTRATO NÃO CONFIRMADO:
O código original usava endpoints não confirmados na documentação oficial da ANVISA:
- https://consultas.anvisa.gov.br/api/medicamentos/{registro_ms}
- https://consultas.anvisa.gov.br/api/medicamentos/busca
- https://consultas.anvisa.gov.br/api/medicamentos/verificar

A documentação oficial (https://api.anvisa.gov.br) mostra endpoints diferentes:
- https://api-gateway.prd.apps.anvisa.gov.br/anvs-listacmed-service/api/v1/listascmed/recuperar-lista-cmed-completa
- https://api-gateway.prd.apps.anvisa.gov.br/consultas-externas-api/api/v1/saude

DEVIDO AO DESALINHAMENTO DE CONTRATO, ESTE MÓDULO ESTÁ DESABILITADO PARA USO OPERACIONAL.
Todas as consultas retornam estado "não verificado" e não aprovam operações automáticas.
Para habilitar, é necessário:
1. Confirmar o contrato correto da API ANVISA
2. Atualizar endpoints, autenticação e parser
3. Validar contra documentação oficial
4. Testar com chamadas reais
"""

import os
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Estados de verificação de medicamento."""
    NOT_VERIFIED = "not_verified"  # Não foi possível verificar (seguro)
    VERIFIED_REQUIRES_PRESCRIPTION = "verified_requires_prescription"  # Verificado e exige receita
    VERIFIED_NO_PRESCRIPTION = "verified_no_prescription"  # Verificado e não exige receita
    SOURCE_UNAVAILABLE = "source_unavailable"  # Fonte indisponível
    SOURCE_ERROR = "source_error"  # Erro na fonte


class ANVISAAPI:
    """Cliente para integração com a API da ANVISA"""

    def __init__(self):
        self.token = os.environ.get('ANVISA_API_TOKEN', '')
        self.contract_confirmed = False  # Contrato não confirmado
        self.base_url = 'https://api-gateway.prd.apps.anvisa.gov.br'  # URL oficial (mas não usado sem confirmação)
        self.timeout = 10  # segundos

    def _get_headers(self) -> Dict[str, str]:
        """Retorna headers de autenticação Bearer Token"""
        if not self.token:
            logger.warning("Token da API ANVISA não configurado")
            return {}

        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def consultar_medicamento(self, registro_ms: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Consulta a situação de um medicamento na base da ANVISA

        Args:
            registro_ms: Número de registro MS do medicamento

        Returns:
            Tuple (sucesso, dados, erro)
        
        NOTA: DESABILITADO ATÉ CONFIRMAÇÃO DE CONTRATO
        """
        if not self.contract_confirmed:
            logger.warning(f"Consulta ANVISA desabilitada para registro {registro_ms}: contrato não confirmado")
            return False, None, "Contrato da API ANVISA não confirmado - endpoint desabilitado"

        if not self.token:
            return False, None, "Token da API ANVISA não configurado"

        # Código comentado até confirmação de contrato
        # endpoint = f"{self.base_url}/medicamentos/{registro_ms}"
        # ... código de chamada seria implementado aqui após confirmação

        return False, None, "Contrato da API ANVISA não confirmado - endpoint desabilitado"

    def verificar_regularidade(self, registro_ms: str) -> Dict[str, any]:
        """
        Verifica a regularidade de um medicamento conforme normas ANVISA

        Args:
            registro_ms: Número de registro MS

        Returns:
            Dicionário com status de regularidade e detalhes
        
        NOTA: DESABILITADO ATÉ CONFIRMAÇÃO DE CONTRATO
        """
        resultado = {
            'registro_ms': registro_ms,
            'status': VerificationStatus.NOT_VERIFIED.value,
            'situacao': 'Não verificado',
            'detalhes': 'Contrato da API ANVISA não confirmado - endpoint desabilitado',
            'data_consulta': datetime.now().isoformat(),
            'fonte': 'API ANVISA (desabilitada)',
            'pode_aprovar': False  # NUNCA aprova automaticamente
        }

        logger.warning(f"Verificação ANVISA desabilitada para registro {registro_ms}: contrato não confirmado")
        return resultado

    def validar_portaria_344(self, registro_ms: str, tarja: str) -> Tuple[bool, Optional[str]]:
        """
        Valida se um medicamento está conforme Portaria 344/98

        Args:
            registro_ms: Número de registro MS
            tarja: Tipo de tarja do medicamento

        Returns:
            Tuple (valido, mensagem)
        
        NOTA: DESABILITADO ATÉ CONFIRMAÇÃO DE CONTRATO
        """
        if not self.contract_confirmed:
            logger.warning(f"Validação Portaria 344 desabilitada para registro {registro_ms}: contrato não confirmado")
            return False, "Contrato da API ANVISA não confirmado - validação desabilitada. Requer revisão manual."

        return False, "Contrato da API ANVISA não confirmado - validação desabilitada"

    def buscar_medicamentos_por_nome(self, nome: str, limite: int = 10) -> Tuple[bool, Optional[list], Optional[str]]:
        """
        Busca medicamentos por nome na base da ANVISA para autocomplete

        Args:
            nome: Nome ou parte do nome do medicamento
            limite: Número máximo de resultados

        Returns:
            Tuple (sucesso, resultados, erro)
        
        NOTA: DESABILITADO ATÉ CONFIRMAÇÃO DE CONTRATO
        """
        if not self.contract_confirmed:
            logger.warning(f"Busca ANVISA desabilitada para '{nome}': contrato não confirmado")
            return False, None, "Contrato da API ANVISA não confirmado - endpoint desabilitado"

        if not self.token:
            return False, None, "Token da API ANVISA não configurado"

        return False, None, "Contrato da API ANVISA não confirmado - endpoint desabilitado"

    def verificar_receita_obrigatoria(self, nome_medicamento: str, tarja: str) -> Dict[str, any]:
        """
        Verifica se um medicamento exige receita obrigatória

        Args:
            nome_medicamento: Nome do medicamento
            tarja: Tipo de tarja do medicamento

        Returns:
            Dicionário com informações sobre exigência de receita
        
        NOTA: DESABILITADO ATÉ CONFIRMAÇÃO DE CONTRATO
        Retorna apenas classificação local por tarja, sem heurística de nome para aprovar
        """
        resultado = {
            'exige_receita': None,  # None = não verificado (não é False)
            'tipo_receita': None,
            'tarja': tarja,
            'mensagem': 'Verificação ANVISA desabilitada - contrato não confirmado',
            'alerta': True,  # Alerta porque não foi verificado
            'status': VerificationStatus.NOT_VERIFIED.value,
            'data_consulta': datetime.now().isoformat(),
            'fonte': 'Tarja local (API ANVISA desabilitada)',
            'pode_aprovar': False  # NUNCA aprova automaticamente
        }

        # Classificação baseada APENAS na tarja informada (sem heurística de nome)
        tarjas_controle = ['Tarja Vermelha', 'Tarja Preta', 'Preto', 'Vermelha', 'Portaria 344']
        if any(t in tarja for t in tarjas_controle):
            resultado['exige_receita'] = True
            resultado['tipo_receita'] = 'Receita de Controle Especial'
            resultado['mensagem'] = 'Medicamento de controle especial (classificação por tarja). Verificação ANVISA desabilitada.'
        elif tarja == 'Tarja Amarela':
            resultado['exige_receita'] = True
            resultado['tipo_receita'] = 'Receita Simples'
            resultado['mensagem'] = 'Medicamento de venda sob prescrição (classificação por tarja). Verificação ANVISA desabilitada.'
        else:
            resultado['exige_receita'] = None  # Não assume isento
            resultado['mensagem'] = 'Não foi possível verificar exigência de receita. Verificação ANVISA desabilitada.'

        logger.warning(f"Verificação de receita ANVISA desabilitada para '{nome_medicamento}': contrato não confirmado")
        return resultado


# Instância global do cliente ANVISA
_anvisa_client: Optional[ANVISAAPI] = None


def obter_cliente_anvisa() -> ANVISAAPI:
    """Retorna a instância do cliente ANVISA"""
    global _anvisa_client
    if _anvisa_client is None:
        _anvisa_client = ANVISAAPI()
    return _anvisa_client


def consultar_regularidade_medicamento(registro_ms: str) -> Dict[str, any]:
    """
    Função de conveniência para consultar regularidade de medicamento

    Args:
        registro_ms: Número de registro MS

    Returns:
        Dicionário com status de regularidade
    """
    cliente = obter_cliente_anvisa()
    return cliente.verificar_regularidade(registro_ms)
