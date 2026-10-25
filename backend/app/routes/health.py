from flask import Blueprint, jsonify
from datetime import datetime
from app.database import db
from sqlalchemy import text

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
    except Exception:
        health_status["services"]["database"] = {
            "status": "unhealthy",
        }
        health_status["status"] = "not_ready"
        return jsonify(health_status), 503

    return jsonify(health_status), 200
