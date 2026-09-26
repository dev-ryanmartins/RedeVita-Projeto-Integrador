from flask import Blueprint, jsonify
from datetime import datetime
from app.database import db
from sqlalchemy import text

health_bp = Blueprint("health", __name__)


@health_bp.route("/healthz")
def health_check():
    """
    Endpoint de health check estruturado para DevOps.
    Retorna status da base de dados e serviços auxiliares em formato JSON.
    Não requer autenticação para permitir monitoramento externo.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": {"status": "unknown", "response_time_ms": 0},
            "cache": {"status": "unknown", "response_time_ms": 0},
        },
    }

    # Verifica conexão com banco de dados
    db_start = datetime.utcnow()
    try:
        db.session.execute(text("SELECT 1"))
        db_end = datetime.utcnow()
        db_response_time = (db_end - db_start).total_seconds() * 1000
        health_status["services"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_response_time, 2),
        }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": 0,
        }
        health_status["status"] = "degraded"

    cache_start = datetime.utcnow()
    try:
        from flask import current_app
        cache = current_app.extensions.get('cache')
        if cache and hasattr(cache, 'set'):
            cache.set('health_check_test', 'ok', timeout=10)
            cache.get('health_check_test')
            cache_end = datetime.utcnow()
            cache_response_time = (cache_end - cache_start).total_seconds() * 1000
            health_status["services"]["cache"] = {
                "status": "healthy",
                "response_time_ms": round(cache_response_time, 2),
            }
        else:
            health_status["services"]["cache"] = {
                "status": "not_configured",
                "response_time_ms": 0,
            }
    except Exception as e:
        health_status["services"]["cache"] = {
            "status": "not_configured",
            "error": str(e),
            "response_time_ms": 0,
        }

    # Determina status geral
    if health_status["services"]["database"]["status"] == "unhealthy":
        health_status["status"] = "unhealthy"
    elif health_status["services"]["cache"]["status"] == "unhealthy":
        health_status["status"] = "degraded"

    return jsonify(health_status), 200 if health_status["status"] == "healthy" else 503
