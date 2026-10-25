"""
Middleware para request-id e logging estruturado.

Este módulo implementa:
- Geração e validação de request-id por requisição
- Propagação de request-id em cabeçalhos de resposta
- Logging estruturado sem dados sensíveis
- Métricas básicas de requisições, erros e latência
"""

import uuid
import time
import re
import logging
from flask import request, g, Response
from functools import wraps
from typing import Optional, Callable
from collections import defaultdict


# Configuração de logger estruturado
logger = logging.getLogger(__name__)


# Validação de request-id: UUID v4 format ou string alfanumérica segura
REQUEST_ID_PATTERN = re.compile(r'^[a-zA-Z0-9\-_]{8,64}$')
REQUEST_ID_MAX_LENGTH = 64


def generate_request_id() -> str:
    """Gera um novo request-id UUID v4."""
    return str(uuid.uuid4())


def validate_request_id(request_id: str) -> bool:
    """Valida formato e tamanho do request-id fornecido pelo cliente."""
    if not request_id:
        return False
    if len(request_id) > REQUEST_ID_MAX_LENGTH:
        return False
    return bool(REQUEST_ID_PATTERN.match(request_id))


def get_or_create_request_id() -> str:
    """Obtém request-id do cabeçalho ou gera um novo."""
    # Tentar obter de cabeçalhos (X-Request-ID ou X-Correlation-ID)
    request_id = request.headers.get('X-Request-ID') or request.headers.get('X-Correlation-ID')
    
    if request_id and validate_request_id(request_id):
        return request_id
    
    # Gerar novo request-id
    return generate_request_id()


def sanitize_for_log(value: str) -> str:
    """Remove dados sensíveis de valores antes de logar."""
    if not value:
        return value
    
    # Remove padrões comuns de dados sensíveis
    # CPF: 000.000.000-00 ou 00000000000
    value = re.sub(r'\d{3}\.\d{3}\.\d{3}-\d{2}', '[CPF]', value)
    value = re.sub(r'\d{11}', '[CPF]', value)
    
    # CNPJ: 00.000.000/0000-00
    value = re.sub(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', '[CNPJ]', value)
    
    # Email: usuario@dominio.com
    value = re.sub(r'\S+@\S+', '[EMAIL]', value)
    
    # Tokens longos (potenciais chaves de API, JWT, etc)
    value = re.sub(r'[A-Za-z0-9_\-]{32,}', '[TOKEN]', value)
    
    return value


# Métricas básicas em memória (apenas para desenvolvimento/teste)
_metrics = defaultdict(lambda: {'count': 0, 'errors': 0, 'total_latency': 0.0})


def record_metric(endpoint: str, status_code: int, latency: float):
    """Registra métrica de requisição."""
    _metrics[endpoint]['count'] += 1
    if status_code >= 400:
        _metrics[endpoint]['errors'] += 1
    _metrics[endpoint]['total_latency'] += latency


def get_metrics() -> dict:
    """Retorna métricas coletadas."""
    result = {}
    for endpoint, data in _metrics.items():
        if data['count'] > 0:
            result[endpoint] = {
                'count': data['count'],
                'errors': data['errors'],
                'avg_latency_ms': round(data['total_latency'] / data['count'] * 1000, 2),
                'error_rate': round(data['errors'] / data['count'] * 100, 2)
            }
    return result


def reset_metrics():
    """Reseta métricas (útil para testes)."""
    global _metrics
    _metrics = defaultdict(lambda: {'count': 0, 'errors': 0, 'total_latency': 0.0})


def request_id_middleware(app):
    """Middleware Flask para gerenciar request-id e logging estruturado."""
    
    @app.before_request
    def before_request_handler():
        # Gerar ou validar request-id
        request_id = get_or_create_request_id()
        g.request_id = request_id
        g.start_time = time.time()
        
        # Log estruturado do início da requisição
        logger.info(
            'request_started',
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': sanitize_for_log(request.path),
                'remote_addr': request.remote_addr,
                'user_agent': request.user_agent.string[:200] if request.user_agent else None
            }
        )
    
    @app.after_request
    def after_request_handler(response: Response) -> Response:
        # Adicionar request-id ao cabeçalho de resposta
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        
        # Calcular latência
        latency = 0.0
        if hasattr(g, 'start_time'):
            latency = time.time() - g.start_time
        
        # Registrar métrica
        endpoint = request.endpoint or request.path
        record_metric(endpoint, response.status_code, latency)
        
        # Log estruturado do fim da requisição
        logger.info(
            'request_completed',
            extra={
                'request_id': g.request_id if hasattr(g, 'request_id') else None,
                'method': request.method,
                'path': sanitize_for_log(request.path),
                'status_code': response.status_code,
                'latency_ms': round(latency * 1000, 2)
            }
        )
        
        return response
    
    @app.errorhandler(Exception)
    def error_handler(error):
        # Log estruturado de erro sem dados sensíveis
        logger.error(
            'request_error',
            extra={
                'request_id': g.request_id if hasattr(g, 'request_id') else None,
                'method': request.method,
                'path': sanitize_for_log(request.path),
                'error_type': type(error).__name__,
                'error_message': str(error)[:500]  # Limitar tamanho
            },
            exc_info=False  # Não logar stack trace completo
        )
        
        # Re-levantar para ser tratado por outros handlers
        raise error
    
    return app


def log_function_call(func: Callable) -> Callable:
    """Decorator para logging estruturado de chamadas de função."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        request_id = g.request_id if hasattr(g, 'request_id') else None
        
        logger.info(
            'function_call',
            extra={
                'request_id': request_id,
                'function': func_name,
                'module': func.__module__
            }
        )
        
        try:
            result = func(*args, **kwargs)
            logger.info(
                'function_success',
                extra={
                    'request_id': request_id,
                    'function': func_name
                }
            )
            return result
        except Exception as e:
            logger.error(
                'function_error',
                extra={
                    'request_id': request_id,
                    'function': func_name,
                    'error_type': type(e).__name__,
                    'error_message': str(e)[:500]
                },
                exc_info=False
            )
            raise
    
    return wrapper
