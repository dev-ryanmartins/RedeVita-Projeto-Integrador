from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.reserva_oferta import ReservaOferta, StatusReserva
from app.models.oferta_medicamento import OfertaMedicamento, StatusOferta
from app.models.instituicao import Instituicao
from app.database import db
from app.core.decorators import admin_required
from app.utils.log_helper import registrar_log
from app.utils.sanitize import limpar
from app.models.movimento_estoque import MovimentoEstoque


reserva_oferta_bp = Blueprint("reserva_mgmt", __name__, url_prefix="/reservas")


@reserva_oferta_bp.route("/")
@login_required
@admin_required
def listar_reservas():
    """Lista todas as reservas de ofertas."""
    reservas = ReservaOferta.query.order_by(ReservaOferta.criado_em.desc()).all()
    ofertas = OfertaMedicamento.query.filter(OfertaMedicamento.status == StatusOferta.DISPONIVEL.value).all()
    instituicoes = Instituicao.query.filter(Instituicao.ativo == True).all()
    return render_template("reservas_ofertas.html", reservas=reservas, ofertas=ofertas, instituicoes=instituicoes)


@reserva_oferta_bp.route("/criar", methods=["POST"])
@login_required
def criar_reserva():
    """Cria uma nova reserva de oferta."""
    oferta_id = request.form.get("oferta_id", type=int)
    instituicao_id = request.form.get("instituicao_id", type=int)
    quantidade_reservada = request.form.get("quantidade_reservada", type=int)
    observacoes = limpar(request.form.get("observacoes", ""))
    
    if not oferta_id:
        flash("Selecione uma oferta.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    if not instituicao_id:
        flash("Selecione uma instituição.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    if not quantidade_reservada or quantidade_reservada <= 0:
        flash("Quantidade reservada deve ser maior que zero.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    oferta = OfertaMedicamento.query.get(oferta_id)
    if not oferta:
        flash("Oferta não encontrada.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    instituicao = Instituicao.query.get(instituicao_id)
    if not instituicao:
        flash("Instituição não encontrada.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se o usuário está vinculado à instituição receptora ou é admin
    if not current_user.is_admin and current_user.instituicao_id != instituicao_id:
        flash("Você não tem permissão para criar reserva para esta instituição.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se a oferta está disponível
    if oferta.status != StatusOferta.DISPONIVEL.value:
        flash("Esta oferta não está disponível para reserva.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se há quantidade disponível suficiente
    if oferta.quantidade_disponivel < quantidade_reservada:
        flash(f"Quantidade insuficiente. Disponível: {oferta.quantidade_disponivel}", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Gera operação_id para idempotência
    operacao_id = MovimentoEstoque.gerar_operacao_id()
    
    try:
        # Cria a reserva dentro de uma transação
        reserva = ReservaOferta(
            oferta_id=oferta_id,
            instituicao_id=instituicao_id,
            quantidade_reservada=quantidade_reservada,
            status=StatusReserva.RESERVADA.value,
            reservado_por_id=current_user.id,
            operacao_id=operacao_id,
            observacoes=observacoes if observacoes else None
        )
        db.session.add(reserva)
        
        # Reserva a quantidade na oferta de forma atômica
        success, nova_quantidade = OfertaMedicamento.reservar_atomico(
            db.session,
            oferta_id,
            quantidade_reservada
        )
        
        if not success:
            db.session.rollback()
            flash("Erro ao reservar quantidade na oferta. Disponibilidade insuficiente.", "danger")
            return redirect(url_for("reserva_oferta.listar_reservas"))
        
        db.session.commit()
        registrar_log(
            "Criação Reserva Oferta",
            f'Reserva {reserva.id} criada: {quantidade_reservada} unidades da oferta {oferta_id} pela instituição {instituicao.nome} por usuário {current_user.id}',
        )
        flash(f"Reserva de {quantidade_reservada} unidades criada com sucesso.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao criar reserva. Tente novamente.", "danger")
    
    return redirect(url_for("reserva_oferta.listar_reservas"))


@reserva_oferta_bp.route("/<int:rid>/confirmar", methods=["POST"])
@login_required
def confirmar_reserva(rid):
    """Confirma uma reserva (pela farmácia doadora)."""
    reserva = db.session.get(ReservaOferta, rid)
    if not reserva:
        flash("Reserva não encontrada.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se o usuário está vinculado à farmácia doadora ou é admin
    if not current_user.is_admin and current_user.farmacia_id != reserva.oferta.farmacia_id:
        flash("Você não tem permissão para confirmar esta reserva.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se a reserva está em status APROVADA (aprovada pelo farmacêutico)
    if reserva.status != StatusReserva.APROVADA.value:
        flash("Esta reserva precisa ser aprovada pelo farmacêutico antes de ser confirmada.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    try:
        if reserva.confirmar(current_user.id):
            # Confirma a oferta também
            if reserva.oferta:
                reserva.oferta.confirmar()
            
            db.session.commit()
            registrar_log(
                "Confirmação Reserva Oferta",
                f'Reserva {reserva.id} confirmada por usuário {current_user.id}',
            )
            flash(f"Reserva {reserva.id} confirmada com sucesso.", "success")
        else:
            flash("Não é possível confirmar esta reserva.", "danger")
    except Exception:
        db.session.rollback()
        flash("Erro ao confirmar reserva. Tente novamente.", "danger")
    
    return redirect(url_for("reserva_oferta.listar_reservas"))


@reserva_oferta_bp.route("/<int:rid>/rejeitar", methods=["POST"])
@login_required
def rejeitar_reserva(rid):
    """Rejeita uma reserva (pela farmácia doadora)."""
    reserva = db.session.get(ReservaOferta, rid)
    if not reserva:
        flash("Reserva não encontrada.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    # Verifica se o usuário está vinculado à farmácia doadora ou é admin
    if not current_user.is_admin and current_user.farmacia_id != reserva.oferta.farmacia_id:
        flash("Você não tem permissão para rejeitar esta reserva.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    motivo = limpar(request.form.get("motivo", ""))
    
    try:
        if reserva.rejeitar(current_user.id, motivo):
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
                "Rejeição Reserva Oferta",
                f'Reserva {reserva.id} rejeitada por usuário {current_user.id}',
            )
            flash(f"Reserva {reserva.id} rejeitada com sucesso.", "success")
        else:
            flash("Não é possível rejeitar esta reserva.", "danger")
    except Exception:
        db.session.rollback()
        flash("Erro ao rejeitar reserva. Tente novamente.", "danger")
    
    return redirect(url_for("reserva_oferta.listar_reservas"))


@reserva_oferta_bp.route("/<int:rid>/cancelar", methods=["POST"])
@login_required
@admin_required
def cancelar_reserva(rid):
    """Cancela uma reserva."""
    reserva = db.session.get(ReservaOferta, rid)
    if not reserva:
        flash("Reserva não encontrada.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    try:
        if reserva.cancelar():
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
                "Cancelamento Reserva Oferta",
                f'Reserva {reserva.id} cancelada',
            )
            flash(f"Reserva {reserva.id} cancelada com sucesso.", "success")
        else:
            flash("Não é possível cancelar esta reserva.", "danger")
    except Exception:
        db.session.rollback()
        flash("Erro ao cancelar reserva. Tente novamente.", "danger")
    
    return redirect(url_for("reserva_oferta.listar_reservas"))


@reserva_oferta_bp.route("/<int:rid>/expirar", methods=["POST"])
@login_required
@admin_required
def expirar_reserva(rid):
    """Expira uma reserva manualmente."""
    reserva = db.session.get(ReservaOferta, rid)
    if not reserva:
        flash("Reserva não encontrada.", "danger")
        return redirect(url_for("reserva_oferta.listar_reservas"))
    
    try:
        if reserva.expirar():
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
                "Expiração Reserva Oferta",
                f'Reserva {reserva.id} expirada',
            )
            flash(f"Reserva {reserva.id} expirada com sucesso.", "success")
        else:
            flash("Não é possível expirar esta reserva.", "danger")
    except Exception:
        db.session.rollback()
        flash("Erro ao expirar reserva. Tente novamente.", "danger")
    
    return redirect(url_for("reserva_oferta.listar_reservas"))
