from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required
from app.models.log_atividade import LogAtividade
from app.core.decorators import admin_required
from app.database import db
from app.utils.log_helper import registrar_log
from datetime import datetime, timedelta
import json

logs_bp = Blueprint("logs", __name__)


@logs_bp.route("/logs")
@login_required
@admin_required
def listar_logs():
    pagina = request.args.get("page", 1, type=int)
    por_pagina = 50
    try:
        logs = LogAtividade.query.order_by(LogAtividade.created_at.desc()).paginate(
            page=pagina, per_page=por_pagina, error_out=False
        )
    except Exception:
        logs = None
    return render_template("logs.html", logs=logs)


@logs_bp.route("/logs/limpar", methods=["POST"])
@login_required
@admin_required
def limpar_logs():
    dias = request.form.get("dias", 90, type=int)
    if dias < 1:
        dias = 90
    data_limite = datetime.utcnow() - timedelta(days=dias)
    try:
        count = LogAtividade.query.filter(LogAtividade.created_at < data_limite).count()
    except Exception:
        count = 0
    try:
        LogAtividade.query.filter(LogAtividade.created_at < data_limite).delete()
        db.session.commit()
    except Exception:
        db.session.rollback()
    try:
        registrar_log(
            "Limpeza de Logs",
            f'{count} registros anteriores a {data_limite.strftime("%d/%m/%Y")} excluídos',
        )
    except Exception:
        pass
    flash(f"{count} log(s) com mais de {dias} dias foram removidos.", "success")
    return redirect(url_for("logs.listar_logs"))


@logs_bp.route("/api/v1/logs/export")
@login_required
@admin_required
def export_logs():
    """
    Exporta o histórico da tabela log_atividade em formato JSON limpo.
    Permite download do arquivo para auditoria externa.
    """
    try:
        # Busca todos os logs (limit to last 1000 for performance)
        logs = LogAtividade.query.order_by(LogAtividade.created_at.desc()).limit(1000).all()
        
        # Converte para formato JSON
        logs_data = []
        for log in logs:
            log_dict = {
                'id': log.id,
                'usuario_id': log.usuario_id,
                'acao': log.acao,
                'detalhes': log.detalhes,
                'ip': log.ip,
                'created_at': log.created_at.isoformat() if log.created_at else None
            }
            logs_data.append(log_dict)
        
        # Cria resposta JSON
        response = Response(
            json.dumps(logs_data, indent=2, ensure_ascii=False),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=logs_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            }
        )
        
        # Registra a exportação
        registrar_log(
            'Exportação de Logs',
            f'Exportados {len(logs_data)} registros de log_atividade'
        )
        
        return response
        
    except Exception as e:
        flash(f"Erro ao exportar logs: {str(e)}", "error")
        return redirect(url_for("logs.listar_logs"))
