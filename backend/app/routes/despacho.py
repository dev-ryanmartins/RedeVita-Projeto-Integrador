from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.reserva_oferta import ReservaOferta, StatusReserva
from app.models.oferta_medicamento import OfertaMedicamento
from app.models.medicamento import Medicamento
from app.models.movimento_estoque import MovimentoEstoque
from app.database import db
from app.utils.log_helper import registrar_log
from app.utils.sanitize import limpar
from app.utils.medication_validation import atomic_reduce_stock_quantity


despacho_bp = Blueprint("despacho", __name__, url_prefix="/despacho")


@despacho_bp.route("/<int:rid>/realizar", methods=["POST"])
@login_required
def realizar_despacho(rid):
    """Realiza o despacho de uma reserva (saída física de estoque)."""
    reserva = db.session.get(ReservaOferta, rid)
    if not reserva:
        flash("Reserva não encontrada.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se a reserva está em status CONFIRMADA
    if reserva.status != StatusReserva.CONFIRMADA.value:
        flash("Esta reserva não pode ser despachada no status atual.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Gera operacao_id para idempotência
    operacao_id = MovimentoEstoque.gerar_operacao_id()
    
    try:
        # Reduz o estoque físico atômicamente usando o método existente
        medicamento = reserva.oferta.medicamento
        
        # Usa atomic_reduce_stock_quantity para garantir atomicidade
        success, new_quantity = atomic_reduce_stock_quantity(
            db.session,
            medicamento.id,
            reserva.quantidade_reservada
        )
        
        if not success:
            db.session.rollback()
            flash(f"Estoque insuficiente. Operação atômica falhou.", "danger")
            return redirect(url_for("reserva_oferta.listar_reservas"))
        
        # Cria movimento de estoque (saída)
        movimento = MovimentoEstoque(
            medicamento_id=medicamento.id,
            quantidade=reserva.quantidade_reservada,
            tipo="saida",
            operacao_id=operacao_id,
            usuario_id=current_user.id,
            autorizado_por_id=current_user.id,
            justificativa=f"Despacho da reserva {reserva.id}"
        )
        db.session.add(movimento)
        
        # Move reserva para DESPACHADA
        if not reserva.despachar():
            db.session.rollback()
            flash("Erro ao despachar reserva.", "danger")
            return redirect(url_for("reserva_oferta.listar_reservas"))
        
        # Move oferta para DESPACHADA
        if not reserva.oferta.despachar():
            db.session.rollback()
            flash("Erro ao despachar oferta.", "danger")
            return redirect(url_for("reserva_oforta.listar_reservas"))
        
        db.session.commit()
        registrar_log(
            "Despacho de Reserva",
            f'Reserva {reserva.id} despachada: {reserva.quantidade_reservada} unidades do medicamento {medicamento.nome}',
        )
        flash(f"Despacho realizado com sucesso. Saída de {reserva.quantidade_reservada} unidades.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao realizar despacho. Tente novamente.", "danger")
    
    return redirect(url_for("reserva_oforta.listar_reservas"))
