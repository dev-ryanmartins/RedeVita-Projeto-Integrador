from flask import Blueprint, jsonify, current_app, g
from datetime import datetime
from app.database import db
from sqlalchemy import text
import logging
import os

logger = logging.getLogger(__name__)

health_bp = Blueprint("health", __name__)


@health_bp.route("/healthz")
def readiness_check():
    """
    Readiness probe: verifica se a aplicação está pronta para atender requisições.
    Verifica dependências necessárias (banco de dados).
    Se o banco estiver indisponível, retorna 503.
    Não expõe DSN, host, credenciais ou detalhes de erro.
    """
    health_status = {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "type": "readiness",
        "services": {
            "database": {"status": "unknown"},
        },
    }

    # Verifica conexão com banco de dados (dependência necessária)
    try:
        db.session.execute(text("SELECT 1"))
        health_status["services"]["database"] = {
            "status": "healthy",
        }
    except Exception as e:
        # Log sanitizado sem expor detalhes da exceção
        logger.warning("Database health check failed: connection unavailable")
        health_status["services"]["database"] = {
            "status": "unhealthy",
        }
        health_status["status"] = "not_ready"
        return jsonify(health_status), 503

    return jsonify(health_status), 200


@health_bp.route("/metrics")
def metrics_endpoint():
    """
    Endpoint de métricas básicas (apenas desenvolvimento/teste).
    Exibe contagem de requisições, erros e latência média por endpoint.
    Disponível apenas em ambiente de desenvolvimento/teste.
    """
    # Verificar se está em ambiente de desenvolvimento/teste
    is_dev = os.environ.get('FLASK_ENV') == 'development' or \
             os.environ.get('APP_DEBUG') == 'true' or \
             current_app.debug
    
    if not is_dev:
        return jsonify({
            "error": "Metrics endpoint is only available in development/test environment"
        }), 403
    
    # Obter métricas do middleware
    from app.core.middleware import get_metrics
    metrics = get_metrics()
    
    return jsonify({
        "timestamp": datetime.utcnow().isoformat(),
        "environment": "development",
        "metrics": metrics,
        "note": "These are in-memory metrics for development/testing only. Do not use for production monitoring."
    }), 200
