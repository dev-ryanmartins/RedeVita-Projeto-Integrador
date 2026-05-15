from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models.log_atividade import LogAtividade
from app.core.decorators import admin_required

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
