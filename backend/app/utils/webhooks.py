"""
Webhooks - Sistema de Webhooks Institucionais
Envia eventos via HTTP POST para ONGs parceiras e secretarias de saúde
Disciplina: Programação Backend com Script - Integrações Externas
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import requests

logger = logging.getLogger(__name__)

# Executor global para envio assíncrono de webhooks
_webhook_executor = ThreadPoolExecutor(max_workers=3)


@dataclass
class WebhookEndpoint:
    """Configuração de um endpoint de webhook"""
    id: int
    nome: str
    url: str
    tipo: str  # 'ong', 'secretaria_saude', 'hospital'
    ativo: bool = True
    headers: Optional[Dict] = None
    eventos: Optional[List[str]] = None  # Lista de eventos que este endpoint recebe


@dataclass
class WebhookEvent:
    """Evento a ser enviado via webhook"""
    tipo: str  # 'medicamento_liberado', 'estoque_critico', 'doacao_registrada'
    dados: Dict
    timestamp: datetime


class WebhookManager:
    """
    Gerenciador de webhooks institucionais.
    Envia eventos para parceiros configurados.
    """
    
    def __init__(self):
        """Inicializa o gerenciador de webhooks"""
        self.endpoints: Dict[int, WebhookEndpoint] = {}
        self._carregar_endpoints()
    
    def _carregar_endpoints(self):
        """
        Carrega endpoints de webhooks configurados.
        Em produção, isso viria do banco de dados.
        """
        # Endpoints de exemplo (em produção, carregar do banco)
        self.endpoints = {
            1: WebhookEndpoint(
                id=1,
                nome='ONG Parceira A',
                url='https://api.ong-exemplo.com/webhook/redevita',
                tipo='ong',
                ativo=True,
                eventos=['medicamento_liberado', 'estoque_critico']
            ),
            2: WebhookEndpoint(
                id=2,
                nome='Secretaria de Saúde Municipal',
                url='https://api.saude.gov.br/webhook/redevita',
                tipo='secretaria_saude',
                ativo=True,
                eventos=['medicamento_liberado']
            )
        }
    
    def adicionar_endpoint(self, endpoint: WebhookEndpoint):
        """
        Adiciona um novo endpoint de webhook.
        
        Args:
            endpoint: Configuração do endpoint
        """
        self.endpoints[endpoint.id] = endpoint
        logger.info(f"Webhook endpoint adicionado: {endpoint.nome}")
    
    def remover_endpoint(self, endpoint_id: int):
        """
        Remove um endpoint de webhook.
        
        Args:
            endpoint_id: ID do endpoint a remover
        """
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            logger.info(f"Webhook endpoint removido: {endpoint_id}")
    
    def enviar_webhook(self, endpoint: WebhookEndpoint, evento: WebhookEvent) -> bool:
        """
        Envia um evento para um endpoint específico.
        
        Args:
            endpoint: Endpoint de destino
            evento: Evento a enviar
        
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        if not endpoint.ativo:
            logger.debug(f"Endpoint {endpoint.nome} está inativo, ignorando")
            return False
        
        # Verifica se o endpoint está inscrito neste tipo de evento
        if endpoint.eventos and evento.tipo not in endpoint.eventos:
            logger.debug(f"Endpoint {endpoint.nome} não está inscrito no evento {evento.tipo}")
            return False
        
        try:
            payload = {
                'event': evento.tipo,
                'timestamp': evento.timestamp.isoformat(),
                'data': evento.dados,
                'source': 'RedeVita'
            }
            
            headers = endpoint.headers or {
                'Content-Type': 'application/json',
                'User-Agent': 'RedeVita-Webhook/1.0'
            }
            
            response = requests.post(
                endpoint.url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Webhook enviado com sucesso para {endpoint.nome}: {response.status_code}")
                return True
            else:
                logger.warning(f"Webhook falhou para {endpoint.nome}: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout ao enviar webhook para {endpoint.nome}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar webhook para {endpoint.nome}: {str(e)}")
            return False
    
    def enviar_webhook_async(self, endpoint: WebhookEndpoint, evento: WebhookEvent):
        """
        Envia webhook de forma assíncrona.
        
        Args:
            endpoint: Endpoint de destino
            evento: Evento a enviar
        """
        def _enviar():
            try:
                self.enviar_webhook(endpoint, evento)
            except Exception as e:
                logger.error(f"Erro no envio assíncrono de webhook: {str(e)}")
        
        _webhook_executor.submit(_enviar)
    
    def enviar_evento(self, evento: WebhookEvent, assincrono: bool = True):
        """
        Envia um evento para todos os endpoints configurados.
        
        Args:
            evento: Evento a enviar
            assincrono: Se True, envia de forma assíncrona
        """
        logger.info(f"Enviando evento {evento.tipo} para {len(self.endpoints)} endpoints")
        
        for endpoint in self.endpoints.values():
            if assincrono:
                self.enviar_webhook_async(endpoint, evento)
            else:
                self.enviar_webhook(endpoint, evento)
    
    def notificar_medicamento_liberado(self, medicamento_id: int, nome: str, principio_ativo: str, 
                                       quantidade: int, farmacia: str):
        """
        Notifica liberação de medicamento do Semáforo Amarelo.
        
        Args:
            medicamento_id: ID do medicamento
            nome: Nome do medicamento
            principio_ativo: Princípio ativo
            quantidade: Quantidade liberada
            farmacia: Nome da farmácia
        """
        evento = WebhookEvent(
            tipo='medicamento_liberado',
            dados={
                'medicamento_id': medicamento_id,
                'nome': nome,
                'principio_ativo': principio_ativo,
                'quantidade': quantidade,
                'farmacia': farmacia,
                'motivo': 'Vencimento próximo (Semáforo Amarelo)'
            },
            timestamp=datetime.utcnow()
        )
        
        self.enviar_evento(evento)
    
    def notificar_estoque_critico(self, medicamento_id: int, nome: str, quantidade: int):
        """
        Notifica estoque crítico de medicamento.
        
        Args:
            medicamento_id: ID do medicamento
            nome: Nome do medicamento
            quantidade: Quantidade atual
        """
        evento = WebhookEvent(
            tipo='estoque_critico',
            dados={
                'medicamento_id': medicamento_id,
                'nome': nome,
                'quantidade': quantidade,
                'nivel': 'CRÍTICO'
            },
            timestamp=datetime.utcnow()
        )
        
        self.enviar_evento(evento)
    
    def notificar_doacao_registrada(self, doacao_id: int, medicamento: str, quantidade: int, 
                                    doador: str):
        """
        Notifica registro de nova doação.
        
        Args:
            doacao_id: ID da doação
            medicamento: Nome do medicamento
            quantidade: Quantidade doada
            doador: Nome do doador
        """
        evento = WebhookEvent(
            tipo='doacao_registrada',
            dados={
                'doacao_id': doacao_id,
                'medicamento': medicamento,
                'quantidade': quantidade,
                'doador': doador
            },
            timestamp=datetime.utcnow()
        )
        
        self.enviar_evento(evento)


# Instância global do gerenciador
_webhook_manager: Optional[WebhookManager] = None


def obter_webhook_manager() -> WebhookManager:
    """
    Obtém a instância global do gerenciador de webhooks.
    """
    global _webhook_manager
    if _webhook_manager is None:
        _webhook_manager = WebhookManager()
    return _webhook_manager


def notificar_medicamento_liberado(medicamento_id: int, nome: str, principio_ativo: str,
                                    quantidade: int, farmacia: str):
    """
    Função conveniente para notificar liberação de medicamento.
    """
    manager = obter_webhook_manager()
    manager.notificar_medicamento_liberado(medicamento_id, nome, principio_ativo, 
                                          quantidade, farmacia)


def notificar_estoque_critico(medicamento_id: int, nome: str, quantidade: int):
    """
    Função conveniente para notificar estoque crítico.
    """
    manager = obter_webhook_manager()
    manager.notificar_estoque_critico(medicamento_id, nome, quantidade)


def notificar_doacao_registrada(doacao_id: int, medicamento: str, quantidade: int, doador: str):
    """
    Função conveniente para notificar registro de doação.
    """
    manager = obter_webhook_manager()
    manager.notificar_doacao_registrada(doacao_id, medicamento, quantidade, doador)
