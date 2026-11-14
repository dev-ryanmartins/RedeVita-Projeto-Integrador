from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.aprovacao_farmaceutica import AprovacaoFarmaceutica, StatusAprovacao
from app.models.reserva_oferta import ReservaOferta, StatusReserva
from app.models.oferta_medicamento import OfertaMedicamento
from app.models.medicamento import Medicamento
from app.models.receita_anexo import ReceitaAnexo
from app.database import db
from app.utils.log_helper import registrar_log
from app.utils.sanitize import limpar
from app.models.movimento_estoque import MovimentoEstoque


aprovacao_farmaceutica_bp = Blueprint("aprovacao_farmaceutica", __name__, url_prefix="/aprovacao")


@aprovacao_farmaceutica_bp.route("/<int:rid>/aprovar", methods=["POST"])
@login_required
def aprovar_reserva(rid):
    """Aprova uma reserva de medicamento (farmacêutico)."""
    reserva = db.session.get(ReservaOferta, rid)
    if not reserva:
        flash("Reserva não encontrada.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se o usuário é farmacêutico
    if current_user.cargo != "Farmacêutico":
        flash("Apenas farmacêuticos podem aprovar reservas.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se o usuário está vinculado à farmácia de origem
    if current_user.farmacia_id != reserva.oferta.farmacia_id:
        flash("Você não tem permissão para aprovar reservas desta farmácia.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se a reserva está em status RESERVADA
    if reserva.status != StatusReserva.RESERVADA.value:
        flash("Esta reserva não pode ser aprovada no status atual.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Se medicamento controlado, validar existência de receita
    if reserva.oferta.medicamento.controlado:
        # Verifica se existe anexo de receita para esta reserva
        anexo_receita = ReceitaAnexo.query.filter_by(reserva_id=reserva.id).first()
        if not anexo_receita:
            flash("Medicamento controlado: receita digitalizada obrigatória. Faça upload da receita antes de aprovar.", "danger")
            return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Gera operacao_id para idempotência
    operacao_id = MovimentoEstoque.gerar_operacao_id()
    
    observacoes = limpar(request.form.get("observacoes", ""))
    
    try:
        # Cria registro de aprovação
        aprovacao = AprovacaoFarmaceutica(
            reserva_id=reserva.id,
            usuario_id=current_user.id,
            status=StatusAprovacao.APROVADA.value,
            observacoes=observacoes if observacoes else None,
            operacao_id=operacao_id
        )
        db.session.add(aprovacao)
        
        # Move reserva para APROVADA
        if not reserva.aprovar():
            db.session.rollback()
            flash("Erro ao aprovar reserva.", "danger")
            return redirect(url_for("reserva_oferta.listar_reservas"))
        
        # Move oferta para APROVADA
        if not reserva.oferta.aprovar():
            db.session.rollback()
            flash("Erro ao aprovar oferta.", "danger")
            return redirect(url_for("reserva_oferta.listar_reservas"))
        
        db.session.commit()
        registrar_log(
            "Aprovação Farmacêutica",
            f'Reserva {reserva.id} aprovada por farmacêutico {current_user.id}',
        )
        flash(f"Reserva {reserva.id} aprovada com sucesso.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao aprovar reserva. Tente novamente.", "danger")
    
    return redirect(url_for("reserva_oferta.listar_reservas"))


@aprovacao_farmaceutica_bp.route("/<int:rid>/rejeitar", methods=["POST"])
@login_required
def rejeitar_reserva(rid):
    """Rejeita uma reserva de medicamento (farmacêutico)."""
    reserva = db.session.get(ReservaOferta, rid)
    if not reserva:
        flash("Reserva não encontrada.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se o usuário é farmacêutico
    if current_user.cargo != "Farmacêutico":
        flash("Apenas farmacêuticos podem rejeitar reservas.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se o usuário está vinculado à farmácia de origem
    if current_user.farmacia_id != reserva.oferta.farmacia_id:
        flash("Você não tem permissão para rejeitar reservas desta farmácia.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se a reserva está em status RESERVADA ou APROVADA
    if reserva.status not in [StatusReserva.RESERVADA.value, StatusReserva.APROVADA.value]:
        flash("Esta reserva não pode ser rejeitada no status atual.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    motivo = limpar(request.form.get("motivo", ""))
    
    # Gera operacao_id para idempotência
    operacao_id = MovimentoEstoque.gerar_operacao_id()
    
    try:
        # Cria registro de aprovação (rejeição)
        aprovacao = AprovacaoFarmaceutica(
            reserva_id=reserva.id,
            usuario_id=current_user.id,
            status=StatusAprovacao.REJEITADA.value,
            observacoes=motivo if motivo else None,
            operacao_id=operacao_id
        )
        db.session.add(aprovacao)
        
        # Rejeita a reserva
        if not reserva.rejeitar(current_user.id, motivo):
            db.session.rollback()
            flash("Erro ao rejeitar reserva.", "danger")
            return redirect(url_for("reserva_oferta.listar_reservas"))
        
        # Libera a quantidade reservada na oferta de forma idempotente
        if reserva.oferta:
            success, _ = OfertaMedicamento.liberar_reserva_atomico(
                db.session,
                reserva.oferta.id,
                reserva.quantidade_reservada
            )
            # Se a liberação falhar (já foi liberada), continua anyway (idempotência)
        
        db.session.commit()
        registrar_log(
            "Rejeição Farmacêutica",
            f'Reserva {reserva.id} rejeitada por farmacêutico {current_user.id}',
        )
        flash(f"Reserva {reserva.id} rejeitada com sucesso.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao rejeitar reserva. Tente novamente.", "danger")
    
    return redirect(url_for("reserva_oferta.listar_reservas"))
