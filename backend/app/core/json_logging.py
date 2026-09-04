"""
JSON Structured Logging - Logging Estruturado em JSON
Configura o módulo nativo de logging do Python para emitir logs em formato JSON
Pronto para ingestão em ferramentas como AWS CloudWatch, Datadog ou ELK
Disciplina: DevOps & Cloud Computing - Logs Estruturados e Observabilidade
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pythonjsonlogger import jsonlogger


class JSONFormatter(logging.Formatter):
    """
    Formatter personalizado para emitir logs em formato JSON estruturado.
    Inclui campos padrão para observabilidade em cloud.
    """
    
    def __init__(self):
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formata o registro de log como JSON.
        
        Args:
            record: Registro de log
        
        Returns:
            String JSON do log
        """
        log_data: Dict[str, Any] = {
            'level': record.levelname,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'message': record.getMessage(),
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Adiciona campos extras se disponíveis
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        
        if hasattr(record, 'endpoint'):
            log_data['endpoint'] = record.endpoint
        
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        
        if hasattr(record, 'response_time_ms'):
            log_data['response_time_ms'] = record.response_time_ms
        
        # Adiciona exceção se houver
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Adiciona campos extras do record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, default=str)


class CloudWatchFormatter(logging.Formatter):
    """
    Formatter otimizado para AWS CloudWatch Logs.
    Segue o formato esperado pelo CloudWatch Logs Insights.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            'timestamp': int(time.time() * 1000),  # Epoch em milissegundos
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Campos adicionais para CloudWatch
        if hasattr(record, 'user_id'):
            log_data['userId'] = record.user_id
        
        if hasattr(record, 'endpoint'):
            log_data['endpoint'] = record.endpoint
        
        if hasattr(record, 'method'):
            log_data['httpMethod'] = record.method
        
        if hasattr(record, 'status_code'):
            log_data['httpStatus'] = record.status_code
        
        if hasattr(record, 'response_time_ms'):
            log_data['duration'] = record.response_time_ms
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


def configurar_logging_json():
    """
    Configura o logging do sistema para usar formato JSON estruturado.
    Deve ser chamado na inicialização da aplicação.
    """
    # Obtém o logger raiz
    root_logger = logging.getLogger()
    
    # Remove handlers existentes
    root_logger.handlers.clear()
    
    # Cria handler para console com formato JSON
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    
    # Adiciona handler ao logger raiz
    root_logger.addHandler(console_handler)
    
    # Define nível de log baseado em variável de ambiente
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Configura loggers específicos
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    return root_logger


def configurar_logging_cloudwatch():
    """
    Configura o logging para AWS CloudWatch Logs.
    Usa formato otimizado para CloudWatch Logs Insights.
    """
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CloudWatchFormatter())
    
    root_logger.addHandler(console_handler)
    
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    return root_logger


def criar_logger_com_contexto(nome: str, **contexto) -> logging.Logger:
    """
    Cria um logger com contexto adicional (user_id, endpoint, etc).
    
    Args:
        nome: Nome do logger
        **contexto: Campos de contexto adicionais
    
    Returns:
        Logger configurado com contexto
    """
    logger = logging.getLogger(nome)
    
    # Adiciona um adapter para injetar contexto
    class ContextAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            kwargs['extra'] = kwargs.get('extra', {})
            for key, value in self.extra.items():
                kwargs['extra'][key] = value
            return msg, kwargs
    
    return ContextAdapter(logger, contexto)


# Import os para variável de ambiente
import os
