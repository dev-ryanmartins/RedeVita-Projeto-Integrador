from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.entrega_institucional import EntregaInstitucional, EstadoEntrega
from app.models.reserva_oferta import ReservaOferta, StatusReserva
from app.database import db
from app.utils.log_helper import registrar_log
from app.utils.sanitize import limpar
from app.models.movimento_estoque import MovimentoEstoque


entrega_institucional_bp = Blueprint("entrega_institucional", __name__, url_prefix="/entrega-institucional")


@entrega_institucional_bp.route("/<int:rid>/despachar", methods=["POST"])
@login_required
def despachar_entrega(rid):
    """Despacha uma entrega institucional (pela farmácia doadora)."""
    entrega = db.session.get(EntregaInstitucional, rid)
    if not entrega:
        flash("Entrega não encontrada.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se o usuário está vinculado à farmácia de origem ou é admin
    farmacia_origem = entrega.reserva.oferta.farmacia_id
    if not current_user.is_admin and current_user.farmacia_id != farmacia_origem:
        flash("Você não tem permissão para despachar esta entrega.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se a reserva está em status DESPACHADA
    if entrega.reserva.status != StatusReserva.DESPACHADA.value:
        flash("A reserva precisa estar despachada antes de despachar a entrega.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Gera operacao_id para idempotência
    operacao_id = MovimentoEstoque.gerar_operacao_id()
    
    try:
        # Despacha a entrega
        if not entrega.despachar(current_user.id):
            db.session.rollback()
            flash("Erro ao despachar entrega.", "danger")
            return redirect(url_for("reserva_oferta.listar_reservas"))
        
        db.session.commit()
        registrar_log(
            "Despacho Entrega Institucional",
            f'Entrega {entrega.id} despachada por usuário {current_user.id}',
        )
        flash(f"Entrega {entrega.id} despachada com sucesso.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao despachar entrega. Tente novamente.", "danger")
    
    return redirect(url_for("reserva_oferta.listar_reservas"))


@entrega_institucional_bp.route("/<int:rid>/receber", methods=["POST"])
@login_required
def receber_entrega(rid):
    """Recebe uma entrega institucional (pela instituição destinatária)."""
    entrega = db.session.get(EntregaInstitucional, rid)
    if not entrega:
        flash("Entrega não encontrada.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se o usuário está vinculado à instituição destinatária
    instituicao_destino = entrega.reserva.instituicao_id
    if not current_user.is_admin and current_user.instituicao_id != instituicao_destino:
        flash("Você não tem permissão para receber esta entrega.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se a entrega está em status DESPACHADA
    if entrega.estado != EstadoEntrega.DESPACHADA.value:
        flash("Esta entrega não está pronta para ser recebida.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se a reserva está em status DESPACHADA
    if entrega.reserva.status != StatusReserva.DESPACHADA.value:
        flash("A reserva precisa estar despachada antes de ser recebida.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    observacoes = limpar(request.form.get("observacoes", ""))
    
    # Gera operacao_id para idempotência
    operacao_id = MovimentoEstoque.gerar_operacao_id()
    
    try:
        # Recebe a entrega
        if not entrega.receber(current_user.id, observacoes):
            db.session.rollback()
            flash("Erro ao receber entrega.", "danger")
            return redirect(url_for("reserva_oferta.listar_reservas"))
        
        db.session.commit()
        registrar_log(
            "Recebimento Entrega Institucional",
            f'Entrega {entrega.id} recebida por usuário {current_user.id}',
        )
        flash(f"Entrega {entrega.id} recebida com sucesso.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao receber entrega. Tente novamente.", "danger")
    
    return redirect(url_for("reserva_oferta.listar_reservas"))


@entrega_institucional_bp.route("/<int:rid>/cancelar", methods=["POST"])
@login_required
def cancelar_entrega(rid):
    """Cancela uma entrega institucional."""
    entrega = db.session.get(EntregaInstitucional, rid)
    if not entrega:
        flash("Entrega não encontrada.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    try:
        if not entrega.cancelar():
            db.session.rollback()
            flash("Não é possível cancelar esta entrega.", "danger")
            return redirect(url_for("reserva_oferta.listar_reservas"))
        
        db.session.commit()
        registrar_log(
            "Cancelamento Entrega Institucional",
            f'Entrega {entrega.id} cancelada',
        )
        flash(f"Entrega {entrega.id} cancelada com sucesso.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao cancelar entrega. Tente novamente.", "danger")
    
    return redirect(url_for("reserva_oferta.listar_reservas"))
