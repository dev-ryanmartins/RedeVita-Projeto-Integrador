"""
Rotas para Agendamento de Entrega entre Participantes Autorizados

NOTA: Funcionalidade Admin-only devido à ausência de vínculo confiável
entre usuários e farmácias no modelo atual.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.database import db
from app.core.decorators import admin_required
from app.models.agendamento_entrega import AgendamentoEntrega, EstadoAgendamento
from app.models.usuario import Usuario
from app.models.farmacia import Farmacia
from datetime import datetime

agendamento_entrega_bp = Blueprint("agendamento_entrega", __name__)


@agendamento_entrega_bp.route("/agendamentos-entrega", methods=["GET", "POST"])
@login_required
@admin_required
def listar_agendamentos():
    """Lista todos os agendamentos."""
    if request.method == "POST":
        # Criar novo agendamento
        farmacia_origem_id = request.form.get("farmacia_origem_id", type=int)
        farmacia_destino_id = request.form.get("farmacia_destino_id", type=int)
        data_hora_inicio_str = request.form.get("data_hora_inicio", "").strip()
        data_hora_fim_str = request.form.get("data_hora_fim", "").strip()
        observacoes = request.form.get("observacoes", "").strip() or None
        
        # Validações básicas
        if not farmacia_origem_id or not farmacia_destino_id:
            flash("Farmácias de origem e destino são obrigatórias.", "danger")
            return redirect(url_for("agendamento_entrega.listar_agendamentos"))
        
        if farmacia_origem_id == farmacia_destino_id:
            flash("Farmácia de origem e destino devem ser diferentes.", "danger")
            return redirect(url_for("agendamento_entrega.listar_agendamentos"))
        
        if not data_hora_inicio_str or not data_hora_fim_str:
            flash("Data e hora são obrigatórias.", "danger")
            return redirect(url_for("agendamento_entrega.listar_agendamentos"))
        
        try:
            data_hora_inicio = datetime.strptime(data_hora_inicio_str, "%Y-%m-%dT%H:%M")
            data_hora_fim = datetime.strptime(data_hora_fim_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Formato de data/hora inválido. Use AAAA-MM-DDTHH:MM.", "danger")
            return redirect(url_for("agendamento_entrega.listar_agendamentos"))
        
        if data_hora_inicio <= datetime.utcnow():
            flash("Data/hora não pode estar no passado.", "danger")
            return redirect(url_for("agendamento_entrega.listar_agendamentos"))
        
        if data_hora_fim <= data_hora_inicio:
            flash("Data/hora fim deve ser posterior à início.", "danger")
            return redirect(url_for("agendamento_entrega.listar_agendamentos"))
        
        try:
            agendamento = AgendamentoEntrega(
                farmacia_origem_id=farmacia_origem_id,
                farmacia_destino_id=farmacia_destino_id,
                data_hora_inicio=data_hora_inicio,
                data_hora_fim=data_hora_fim,
                estado=EstadoAgendamento.PROPOSTA.value,
                criado_por_id=current_user.id,
                observacoes=observacoes
            )
            db.session.add(agendamento)
            db.session.commit()
            flash("Agendamento criado com sucesso.", "success")
        except Exception:
            db.session.rollback()
            flash("Erro ao criar agendamento. Tente novamente.", "danger")
        
        return redirect(url_for("agendamento_entrega.listar_agendamentos"))
    
    # Filtros
    estado_filtro = request.args.get("estado", "").strip()
    
    query = AgendamentoEntrega.query
    
    if estado_filtro:
        query = query.filter(AgendamentoEntrega.estado == estado_filtro)
    
    agendamentos = query.order_by(AgendamentoEntrega.data_hora_inicio.desc()).all()
    farmacias = Farmacia.query.all()
    
    return render_template(
        "agendamentos_entrega.html",
        agendamentos=agendamentos,
        farmacias=farmacias,
        estado_filtro=estado_filtro
    )


@agendamento_entrega_bp.route("/agendamentos-entrega/<int:id>/confirmar-origem", methods=["POST"])
@login_required
@admin_required
def confirmar_origem(id):
    """Confirma agendamento pela origem."""
    agendamento = AgendamentoEntrega.query.get_or_404(id)
    
    try:
        agendamento.confirmado_origem_por_id = current_user.id
        agendamento.confirmado_origem_em = datetime.utcnow()
        
        # Atualizar estado
        if agendamento.confirmado_destino_por_id:
            agendamento.estado = EstadoAgendamento.CONFIRMADO.value
        else:
            agendamento.estado = EstadoAgendamento.AGUARDANDO_DESTINO.value
        
        db.session.commit()
        flash("Confirmação da origem registrada.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao confirmar. Tente novamente.", "danger")
    
    return redirect(url_for("agendamento_entrega.listar_agendamentos"))


@agendamento_entrega_bp.route("/agendamentos-entrega/<int:id>/confirmar-destino", methods=["POST"])
@login_required
@admin_required
def confirmar_destino(id):
    """Confirma agendamento pelo destino."""
    agendamento = AgendamentoEntrega.query.get_or_404(id)
    
    try:
        agendamento.confirmado_destino_por_id = current_user.id
        agendamento.confirmado_destino_em = datetime.utcnow()
        
        # Atualizar estado
        if agendamento.confirmado_origem_por_id:
            agendamento.estado = EstadoAgendamento.CONFIRMADO.value
        else:
            agendamento.estado = EstadoAgendamento.AGUARDANDO_ORIGEM.value
        
        db.session.commit()
        flash("Confirmação do destino registrada.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao confirmar. Tente novamente.", "danger")
    
    return redirect(url_for("agendamento_entrega.listar_agendamentos"))


@agendamento_entrega_bp.route("/agendamentos-entrega/<int:id>/cancelar", methods=["POST"])
@login_required
@admin_required
def cancelar_agendamento(id):
    """Cancela um agendamento."""
    agendamento = AgendamentoEntrega.query.get_or_404(id)
    
    motivo = request.form.get("motivo", "").strip() or None
    
    try:
        agendamento.estado = EstadoAgendamento.CANCELADO.value
        agendamento.cancelado_por_id = current_user.id
        agendamento.cancelado_em = datetime.utcnow()
        agendamento.motivo_cancelamento = motivo
        db.session.commit()
        flash("Agendamento cancelado.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao cancelar. Tente novamente.", "danger")
    
    return redirect(url_for("agendamento_entrega.listar_agendamentos"))


@agendamento_entrega_bp.route("/agendamentos-entrega/<int:id>/detalhes")
@login_required
@admin_required
def detalhes_agendamento(id):
    """Detalhes de um agendamento."""
    agendamento = AgendamentoEntrega.query.get_or_404(id)
    return render_template("agendamento_detalhes.html", agendamento=agendamento)
