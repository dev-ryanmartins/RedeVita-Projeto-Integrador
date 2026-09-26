"""
Integração com a API da ANVISA para validação de medicamentos e registros sanitários
Conforme RDC 430/2020 - Consulta de regularidade de medicamentos
"""

import os
import logging
import requests
from typing import Dict, Optional, Tuple
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)


def mapear_tarja_por_principio_ativo(nome_medicamento: str, principio_ativo: str = None) -> str:
    """
    Mapeia automaticamente a tarja com base no princípio ativo ou nome do medicamento.
    Usado para garantir que medicamentos controlados sejam classificados corretamente.
    
    Args:
        nome_medicamento: Nome do medicamento
        principio_ativo: Princípio ativo (opcional)
    
    Returns:
        Tarja classificada
    """
    # Normaliza para comparação
    nome_lower = nome_medicamento.lower()
    principio_lower = (principio_ativo or "").lower()
    
    # Lista de princípios ativos controlados por categoria
    # Portaria 344 (Tarja Preta/A1/A2/A3)
    portaria_344_keywords = [
        'morfina', 'fentanila', 'metadona', 'oxicodona', 'codeína', 'sufentanila',
        'hidromorfona', 'petidina', 'tramadol', 'buprenorfina',
        'metilfenidato', 'lisdexanfetamina', 'modafinila',
        'alprazolam', 'diazepam', 'clonazepam', 'lorazepam', 'bromazepam',
        'nitrazepam', 'midazolam', 'zolpidem', 'zopiclona', 'clobazam',
        'cloxazolam', 'flunitrazepam', 'estazolam', 'oxazepam', 'eszopiclona',
        'alfazolam', 'flurazepam', 'halazepam'
    ]
    
    # Tarja Vermelha (Anti-inflamatórios não esteroides)
    tarja_vermelha_keywords = [
        'ibuprofeno', 'naproxeno', 'diclofenaco', 'nimesulida', 'meloxicam',
        'celecoxibe', 'etoricoxibe', 'indometacina', 'piroxicam', 'cetoprofeno',
        'tenoxicam'
    ]
    
    # Tarja Amarela (Antibióticos)
    tarja_amarela_keywords = [
        'amoxicilina', 'azitromicina', 'ciprofloxacino', 'levofloxacino',
        'claritromicina', 'doxiciclina', 'cefalexina', 'ceftriaxona'
    ]
    
    # Verifica Portaria 344
    for keyword in portaria_344_keywords:
        if keyword in principio_lower or keyword in nome_lower:
            return "Portaria 344"
    
    # Verifica Tarja Vermelha
    for keyword in tarja_vermelha_keywords:
        if keyword in principio_lower or keyword in nome_lower:
            return "Tarja Vermelha"
    
    # Verifica Tarja Amarela
    for keyword in tarja_amarela_keywords:
        if keyword in principio_lower or keyword in nome_lower:
            return "Tarja Amarela"
    
    # Padrão: Sem Tarja
    return "Sem Tarja"


class ANVISAAPI:
    """Cliente para integração com a API da ANVISA"""

    def __init__(self):
        self.token = os.environ.get('ANVISA_API_TOKEN', '')
        self.base_url = 'https://consultas.anvisa.gov.br/api'
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
        """
        if not self.token:
            return False, None, "Token da API ANVISA não configurado"

        endpoint = f"{self.base_url}/medicamentos/{registro_ms}"

        try:
            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                timeout=self.timeout
            )

            if response.status_code == 200:
                dados = response.json()
                logger.info(f"Consulta ANVISA bem-sucedida para registro {registro_ms}")
                return True, dados, None
            elif response.status_code == 404:
                return False, None, f"Registro {registro_ms} não encontrado na base ANVISA"
            elif response.status_code == 401:
                return False, None, "Token de autenticação inválido ou expirado"
            else:
                return False, None, f"Erro na consulta ANVISA: HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            logger.error(f"Timeout na consulta ANVISA para registro {registro_ms}")
            return False, None, "Timeout na conexão com API ANVISA"
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão com API ANVISA: {str(e)}")
            return False, None, f"Erro de conexão: {str(e)}"
        except Exception as e:
            logger.error(f"Erro inesperado na consulta ANVISA: {str(e)}")
            return False, None, f"Erro inesperado: {str(e)}"

    def verificar_regularidade(self, registro_ms: str) -> Dict[str, any]:
        """
        Verifica a regularidade de um medicamento conforme normas ANVISA

        Args:
            registro_ms: Número de registro MS

        Returns:
            Dicionário com status de regularidade e detalhes
        """
        resultado = {
            'registro_ms': registro_ms,
            'regular': True,
            'situacao': 'Desconhecido',
            'detalhes': '',
            'data_consulta': datetime.now().isoformat(),
            'fonte': 'API ANVISA'
        }

        sucesso, dados, erro = self.consultar_medicamento(registro_ms)

        if not sucesso:
            # Fallback seguro: retorna como desconhecido sem bloquear o sistema
            resultado['regular'] = None
            resultado['situacao'] = 'Não foi possível verificar'
            resultado['detalhes'] = erro or 'Erro na comunicação com API ANVISA'
            logger.warning(f"Fallback ANVISA para registro {registro_ms}: {erro}")
            return resultado

        # Analisa a resposta da API
        if dados:
            situacao = dados.get('situacao', '').upper()

            if 'SUSPENSO' in situacao or 'CANCELADO' in situacao or 'VENCIDO' in situacao:
                resultado['regular'] = False
                resultado['situacao'] = situacao
                resultado['detalhes'] = f"Registro com situação irregular: {situacao}"
            elif 'ATIVO' in situacao or 'REGULAR' in situacao:
                resultado['regular'] = True
                resultado['situacao'] = situacao
                resultado['detalhes'] = f"Registro regular: {situacao}"
            else:
                resultado['regular'] = None
                resultado['situacao'] = situacao
                resultado['detalhes'] = f"Situação não categorizada: {situacao}"

        return resultado

    def validar_portaria_344(self, registro_ms: str, tarja: str) -> Tuple[bool, Optional[str]]:
        """
        Valida se um medicamento está conforme Portaria 344/98

        Args:
            registro_ms: Número de registro MS
            tarja: Tipo de tarja do medicamento

        Returns:
            Tuple (valido, mensagem)
        """
        if tarja == "Portaria 344":
            sucesso, dados, erro = self.consultar_medicamento(registro_ms)

            if not sucesso:
                # Fallback: permite cadastro com aviso
                return True, f"Não foi possível validar na ANVISA ({erro}). Cadastro permitido com ressalvas."

            if dados:
                situacao = dados.get('situacao', '').upper()
                if 'SUSPENSO' in situacao or 'CANCELADO' in situacao:
                    return False, f"Registro {registro_ms} está {situacao} na ANVISA. Medicamento não pode ser cadastrado."
                elif 'RESTRITO' in situacao:
                    return True, f"Registro {registro_ms} possui restrições na ANVISA. Cadastro permitido com monitoramento."

        return True, "Validação Portaria 344 concluída com sucesso."

    def buscar_medicamentos_por_nome(self, nome: str, limite: int = 10) -> Tuple[bool, Optional[list], Optional[str]]:
        """
        Busca medicamentos por nome na base da ANVISA para autocomplete

        Args:
            nome: Nome ou parte do nome do medicamento
            limite: Número máximo de resultados

        Returns:
            Tuple (sucesso, resultados, erro)
        """
        if not self.token:
            return False, None, "Token da API ANVISA não configurado"

        endpoint = f"{self.base_url}/medicamentos/busca"
        params = {'nome': nome, 'limite': limite}

        try:
            response = requests.get(
                endpoint,
                headers=self._get_headers(),
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                dados = response.json()
                resultados = dados.get('medicamentos', [])
                
                # Enriquece resultados com tarja mapeada automaticamente
                for med in resultados:
                    if 'tarja' not in med or not med['tarja']:
                        med['tarja'] = self._mapear_tarja_por_nome(med.get('nome', ''), med.get('principio_ativo', ''))
                
                logger.info(f"Busca ANVISA bem-sucedida para '{nome}': {len(resultados)} resultados")
                return True, resultados, None
            elif response.status_code == 404:
                return True, [], "Nenhum medicamento encontrado"
            elif response.status_code == 401:
                return False, None, "Token de autenticação inválido ou expirado"
            else:
                return False, None, f"Erro na busca ANVISA: HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            logger.error(f"Timeout na busca ANVISA para '{nome}'")
            return False, None, "Timeout na conexão com API ANVISA"
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão com API ANVISA: {str(e)}")
            return False, None, f"Erro de conexão: {str(e)}"
        except Exception as e:
            logger.error(f"Erro inesperado na busca ANVISA: {str(e)}")
            return False, None, f"Erro inesperado: {str(e)}"
    
    def _mapear_tarja_por_nome(self, nome: str, principio_ativo: str = None) -> str:
        """
        Mapeia automaticamente a tarja com base no nome ou princípio ativo
        Usado para sincronização com a API ANVISA
        """
        nome_lower = nome.lower()
        principio_lower = (principio_ativo or "").lower()
        
        # Portaria 344 (controle especial)
        portaria_344_keywords = [
            'morfina', 'fentanila', 'metadona', 'oxicodona', 'codeína', 'sufentanila',
            'hidromorfona', 'petidina', 'tramadol', 'buprenorfina',
            'metilfenidato', 'lisdexanfetamina', 'modafinila',
            'alprazolam', 'diazepam', 'clonazepam', 'lorazepam', 'bromazepam',
            'nitrazepam', 'midazolam', 'zolpidem', 'zopiclona', 'clobazam',
            'cloxazolam', 'flunitrazepam', 'estazolam', 'oxazepam', 'eszopiclona',
            'alfazolam', 'flurazepam', 'halazepam'
        ]
        
        # Tarja Vermelha
        tarja_vermelha_keywords = [
            'ibuprofeno', 'naproxeno', 'diclofenaco', 'nimesulida', 'meloxicam',
            'celecoxibe', 'etoricoxibe', 'indometacina', 'piroxicam', 'cetoprofeno',
            'tenoxicam'
        ]
        
        # Tarja Amarela
        tarja_amarela_keywords = [
            'amoxicilina', 'azitromicina', 'ciprofloxacino', 'levofloxacino',
            'claritromicina', 'doxiciclina', 'cefalexina', 'ceftriaxona'
        ]
        
        for keyword in portaria_344_keywords:
            if keyword in principio_lower or keyword in nome_lower:
                return "Portaria 344"
        
        for keyword in tarja_vermelha_keywords:
            if keyword in principio_lower or keyword in nome_lower:
                return "Tarja Vermelha"
        
        for keyword in tarja_amarela_keywords:
            if keyword in principio_lower or keyword in nome_lower:
                return "Tarja Amarela"
        
        return "Sem Tarja"

    def verificar_receita_obrigatoria(self, nome_medicamento: str, tarja: str) -> Dict[str, any]:
        """
        Verifica se um medicamento exige receita obrigatória

        Args:
            nome_medicamento: Nome do medicamento
            tarja: Tipo de tarja do medicamento

        Returns:
            Dicionário com informações sobre exigência de receita
        """
        resultado = {
            'exige_receita': False,
            'tipo_receita': None,
            'tarja': tarja,
            'mensagem': '',
            'alerta': False
        }

        # Verificação baseada na tarja (Portaria 344)
        tarjas_controle = ['Tarja Vermelha', 'Tarja Preta', 'Preto', 'Vermelha']
        if any(t in tarja for t in tarjas_controle):
            resultado['exige_receita'] = True
            resultado['tipo_receita'] = 'Receita de Controle Especial'
            resultado['mensagem'] = 'Medicamento de controle especial - Exige receita de controle especial (RC1) conforme Portaria 344/98'
            resultado['alerta'] = True
        elif tarja == 'Tarja Amarela':
            resultado['exige_receita'] = True
            resultado['tipo_receita'] = 'Receita Simples'
            resultado['mensagem'] = 'Medicamento de venda sob prescrição - Exige receita simples'
            resultado['alerta'] = False
        else:
            resultado['exige_receita'] = False
            resultado['tipo_receita'] = None
            resultado['mensagem'] = 'Medicamento isento de prescrição'
            resultado['alerta'] = False

        # Consulta API ANVISA para informações adicionais (se disponível)
        if self.token:
            try:
                # Tenta buscar informações detalhadas
                endpoint = f"{self.base_url}/medicamentos/verificar"
                params = {'nome': nome_medicamento}
                
                response = requests.get(
                    endpoint,
                    headers=self._get_headers(),
                    params=params,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    dados = response.json()
                    controle_especial = dados.get('controle_especial', False)
                    receita_retida = dados.get('receita_retida', False)
                    
                    if controle_especial or receita_retida:
                        resultado['exige_receita'] = True
                        resultado['tipo_receita'] = 'Receita de Controle Especial'
                        resultado['mensagem'] = f"Medicamento classificado como controle especial pela ANVISA"
                        resultado['alerta'] = True
            except Exception as e:
                logger.warning(f"Não foi possível verificar detalhes na API ANVISA: {str(e)}")
                # Continua com verificação baseada na tarja

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
