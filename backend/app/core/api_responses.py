import uuid
from flask import jsonify, g, request


def _get_or_create_correlation_id():
    """Obtém ou cria um correlation_id para a requisição."""
    if hasattr(g, 'correlation_id'):
        return g.correlation_id
    
    # Tenta obter do header X-Correlation-ID ou X-Request-ID
    correlation_id = request.headers.get('X-Correlation-ID') or request.headers.get('X-Request-ID')
    
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
    
    g.correlation_id = correlation_id
    return correlation_id


def resposta_ok(dados=None, mensagem=None, status=200):
    """Resposta de sucesso padronizada com correlation_id."""
    correlation_id = _get_or_create_correlation_id()
    
    corpo = {
        "sucesso": True,
        "success": True,
        "correlation_id": correlation_id
    }
    
    if mensagem:
        corpo["mensagem"] = mensagem
    if dados is not None:
        corpo["dados"] = dados
        corpo["data"] = dados
    
    return jsonify(corpo), status


def resposta_erro(codigo, mensagem_publica=None, status=400, detalhes=None):
    """
    Resposta de erro padronizada com correlation_id.
    
    Args:
        codigo: Código de erro legível por máquina (ex: "VALIDATION_ERROR", "NOT_FOUND")
        mensagem_publica: Mensagem genérica apropriada para o usuário
        status: Código HTTP
        detalhes: Detalhes adicionais (opcional, sem dados sensíveis)
    """
    correlation_id = _get_or_create_correlation_id()
    
    corpo = {
        "sucesso": False,
        "success": False,
        "erro": {
            "codigo": codigo,
            "mensagem": mensagem_publica or "Erro ao processar requisição",
            "correlation_id": correlation_id
        }
    }
    
    if detalhes:
        corpo["erro"]["detalhes"] = detalhes
    
    return jsonify(corpo), status


# Códigos de erro padronizados
ERRO_VALIDACAO = "VALIDATION_ERROR"
ERRO_NAO_AUTORIZADO = "UNAUTHORIZED"
ERRO_PROIBIDO = "FORBIDDEN"
ERRO_NAO_ENCONTRADO = "NOT_FOUND"
ERRO_CONFLITO = "CONFLICT"
ERRO_INTERNO = "INTERNAL_ERROR"
ERRO_SERVICO_INDISPONIVEL = "SERVICE_UNAVAILABLE"
ERRO_TIMEOUT = "TIMEOUT"
ERRO_INTEGRACAO_EXTERNA = "EXTERNAL_INTEGRATION_ERROR"
