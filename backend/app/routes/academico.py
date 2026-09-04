"""Recursos acadêmicos complementares e isolados do RedeVita."""

from datetime import datetime

from flask import Blueprint, render_template, request
from flask_login import login_required
from sqlalchemy import or_

from app.core.api_responses import resposta_erro, resposta_ok
from app.core.decorators import admin_required
from app.database import db
from app.models.farmacia import Farmacia
from app.models.log_atividade import LogAtividade
from app.models.medicamento import Medicamento
from app.models.paciente import Paciente
from app.utils.iot_telemetry import iot_simulator
from app.utils.trie_busca import buscar_entidades_rapida


academico_bp = Blueprint("academico", __name__)


def _serializar_log(log: LogAtividade) -> dict:
    return {
        "id": log.id,
        "acao": log.acao,
        "detalhes": log.detalhes,
        "ip": log.ip,
        "usuario": log.usuario.nome if log.usuario else "Sistema",
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def _serializar_farmacia(farmacia: Farmacia) -> dict:
    return {
        "id": farmacia.id,
        "nome_fantasia": farmacia.nome_fantasia,
        "razao_social": farmacia.razao_social,
        "cnpj": farmacia.cnpj,
        "responsavel": farmacia.responsavel,
        "endereco": farmacia.endereco,
        "created_at": farmacia.created_at.isoformat() if farmacia.created_at else None,
    }


@academico_bp.route("/monitoramento-iot")
@login_required
def monitoramento_iot():
    """Painel complementar para a simulação de cadeia de frio."""
    sensores = iot_simulator.obter_todas_leituras()
    return render_template(
        "monitoramento_iot.html",
        sensores=sensores,
        alertas=sum(1 for sensor in sensores if sensor["status"] != "NORMAL"),
        atualizado_em=datetime.utcnow().isoformat(),
    )


@academico_bp.route("/api/v1/monitoramento-iot/snapshot")
@login_required
def snapshot_iot():
    """Retorna uma nova fotografia dos sensores simulados para polling do painel."""
    try:
        sensores = iot_simulator.obter_todas_leituras()
        alertas = [sensor for sensor in sensores if sensor["status"] != "NORMAL"]
        return resposta_ok(
            {
                "sensores": sensores,
                "total": len(sensores),
                "alertas": len(alertas),
                "atualizado_em": datetime.utcnow().isoformat(),
            }
        )
    except Exception:
        return resposta_erro("Não foi possível consultar a telemetria simulada.", 500)


@academico_bp.route("/auditoria")
@login_required
@admin_required
def auditoria():
    """Visão administrativa complementar de farmácias e movimentações."""
    farmacias = Farmacia.query.order_by(Farmacia.id.desc()).limit(50).all()
    logs = LogAtividade.query.order_by(LogAtividade.created_at.desc()).limit(50).all()
    # O template legado de auditoria de validade permanece intocado; a visão
    # administrativa complementar usa uma superfície própria.
    return render_template("auditoria_complementar.html", farmacias=farmacias, logs=logs)


@academico_bp.route("/api/v1/auditoria/farmacias")
@login_required
@admin_required
def auditoria_farmacias():
    farmacias = Farmacia.query.order_by(Farmacia.id.desc()).limit(100).all()
    return resposta_ok(
        {
            "farmacias": [_serializar_farmacia(farmacia) for farmacia in farmacias],
            "total": Farmacia.query.count(),
        }
    )


@academico_bp.route("/api/v1/auditoria/movimentacoes")
@login_required
@admin_required
def auditoria_movimentacoes():
    limite_param = request.args.get("limit", 50, type=int) or 50
    limite = max(1, min(limite_param, 100))
    termo = request.args.get("q", "").strip()
    query = LogAtividade.query
    if termo:
        filtro = f"%{termo}%"
        query = query.filter(
            or_(
                LogAtividade.acao.ilike(filtro),
                LogAtividade.detalhes.ilike(filtro),
            )
        )
    logs = query.order_by(LogAtividade.created_at.desc()).limit(limite).all()
    return resposta_ok({"movimentacoes": [_serializar_log(log) for log in logs]})


@academico_bp.route("/api/v1/busca/rapida")
@login_required
def busca_rapida():
    """Sugestões por prefixo usando Trie, sem substituir /buscar."""
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return resposta_ok([])

    tipo = request.args.get("tipo", "todos")
    if tipo not in {"todos", "medicamentos", "pacientes"}:
        return resposta_erro("Tipo de busca inválido.", 400)

    medicamentos = Medicamento.query.all() if tipo in {"todos", "medicamentos"} else []
    pacientes = Paciente.query.all() if tipo in {"todos", "pacientes"} else []
    return resposta_ok(
        buscar_entidades_rapida(query, medicamentos, pacientes, limite=20)
    )