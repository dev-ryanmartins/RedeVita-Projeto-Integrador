from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.campanha import Campanha
from app.database import db
from app.core.decorators import admin_required, equipe_clinica_required
from datetime import datetime, date

campanhas_bp = Blueprint("campanhas", __name__)


@campanhas_bp.route("/campanhas")
@login_required
@equipe_clinica_required
def listar_campanhas():
    """Lista todas as campanhas e alertas comunitários"""
    campanhas = Campanha.query.order_by(Campanha.created_at.desc()).all()
    
    # Contadores por tipo
    arrecadacao = Campanha.query.filter_by(tipo='arrecadacao', status='ativa').count()
    alertas = Campanha.query.filter_by(tipo='alerta', status='ativa').count()
    informativos = Campanha.query.filter_by(tipo='informativo', status='ativa').count()
    
    return render_template(
        "campanhas.html",
        campanhas=campanhas,
        arrecadacao=arrecadacao,
        alertas=alertas,
        informativos=informativos
    )


@campanhas_bp.route("/campanha/nova", methods=["POST"])
@login_required
@admin_required
def nova_campanha():
    """Cria uma nova campanha ou alerta"""
    titulo = request.form.get("titulo", "").strip()
    descricao = request.form.get("descricao", "").strip()
    tipo = request.form.get("tipo", "").strip()
    data_inicio_str = request.form.get("data_inicio", "").strip()
    data_fim_str = request.form.get("data_fim", "").strip()
    
    if not titulo or not descricao or not tipo or not data_inicio_str:
        flash("Preencha todos os campos obrigatórios.", "danger")
        return redirect(url_for("campanhas.listar_campanhas"))
    
    try:
        data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
        data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date() if data_fim_str else None
    except ValueError:
        flash("Data inválida.", "danger")
        return redirect(url_for("campanhas.listar_campanhas"))
    
    campanha = Campanha(
        titulo=titulo,
        descricao=descricao,
        tipo=tipo,
        data_inicio=data_inicio,
        data_fim=data_fim,
        status='ativa',
        criador_id=current_user.id if current_user.is_authenticated else None
    )
    
    db.session.add(campanha)
    db.session.commit()
    
    flash("Campanha criada com sucesso!", "success")
    return redirect(url_for("campanhas.listar_campanhas"))


@campanhas_bp.route("/campanha/<int:campanha_id>/toggle-status", methods=["POST"])
@login_required
@admin_required
def toggle_status(campanha_id):
    """Alterna o status de uma campanha"""
    campanha = db.session.get(Campanha, campanha_id)
    if not campanha:
        flash("Campanha não encontrada.", "danger")
        return redirect(url_for("campanhas.listar_campanhas"))
    
    if campanha.status == 'ativa':
        campanha.status = 'concluida'
    else:
        campanha.status = 'ativa'
    
    db.session.commit()
    flash("Status da campanha atualizado!", "success")
    return redirect(url_for("campanhas.listar_campanhas"))
