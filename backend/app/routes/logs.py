from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.log_atividade import LogAtividade
from app.core.decorators import admin_required
from app.database import db
from app.utils.log_helper import registrar_log
from datetime import datetime, timedelta

logs_bp = Blueprint('logs', __name__)


@logs_bp.route('/logs')
@login_required
@admin_required
def listar_logs():
    pagina = request.args.get('page', 1, type=int)
    por_pagina = 50
    logs = (
        LogAtividade.query
        .order_by(LogAtividade.created_at.desc())
        .paginate(page=pagina, per_page=por_pagina, error_out=False)
    )
    return render_template('logs.html', logs=logs)


@logs_bp.route('/logs/limpar', methods=['POST'])
@login_required
@admin_required
def limpar_logs():
    dias = request.form.get('dias', 90, type=int)
    if dias < 1:
        dias = 90
    data_limite = datetime.utcnow() - timedelta(days=dias)
    count = LogAtividade.query.filter(LogAtividade.created_at < data_limite).count()
    LogAtividade.query.filter(LogAtividade.created_at < data_limite).delete()
    db.session.commit()
    registrar_log('Limpeza de Logs', f'{count} registros anteriores a {data_limite.strftime("%d/%m/%Y")} excluídos')
    flash(f'{count} log(s) com mais de {dias} dias foram removidos.', 'success')
    return redirect(url_for('logs.listar_logs'))
