from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.oferta_medicamento import OfertaMedicamento, StatusOferta
from app.models.medicamento import Medicamento
from app.models.farmacia import Farmacia
from app.database import db
from app.core.decorators import admin_required
from app.utils.log_helper import registrar_log
from app.utils.sanitize import limpar


oferta_medicamento_bp = Blueprint("oferta_mgmt", __name__, url_prefix="/ofertas")


@oferta_medicamento_bp.route("/")
@login_required
@admin_required
def listar_ofertas():
    """Lista todas as ofertas de medicamentos."""
    ofertas = OfertaMedicamento.query.order_by(OfertaMedicamento.criado_em.desc()).all()
    farmacias = Farmacia.query.all()
    medicamentos = Medicamento.query.filter(Medicamento.ativo == True).all()
    return render_template("ofertas_medicamentos.html", ofertas=ofertas, farmacias=farmacias, medicamentos=medicamentos)


@oferta_medicamento_bp.route("/criar", methods=["POST"])
@login_required
@admin_required
def criar_oferta():
    """Cria uma nova oferta de medicamento."""
    farmacia_id = request.form.get("farmacia_id", type=int)
    medicamento_id = request.form.get("medicamento_id", type=int)
    quantidade_ofertada = request.form.get("quantidade_ofertada", type=int)
    data_expiracao = request.form.get("data_expiracao", "")
    observacoes = limpar(request.form.get("observacoes", ""))
    
    if not farmacia_id:
        flash("Selecione uma farmácia.", "danger")
        return redirect(url_for("oferta_medicamento.listar_ofertas"))
    
    if not medicamento_id:
        flash("Selecione um medicamento.", "danger")
        return redirect(url_for("oferta_medicamento.listar_ofertas"))
    
    if not quantidade_ofertada or quantidade_ofertada <= 0:
        flash("Quantidade ofertada deve ser maior que zero.", "danger")
        return redirect(url_for("oferta_medicamento.listar_ofertas"))
    
    farmacia = Farmacia.query.get(farmacia_id)
    if not farmacia:
        flash("Farmácia não encontrada.", "danger")
        return redirect(url_for("oferta_medicamento.listar_ofertas"))
    
    medicamento = Medicamento.query.get(medicamento_id)
    if not medicamento:
        flash("Medicamento não encontrado.", "danger")
        return redirect(url_for("oferta_medicamento.listar_ofertas"))
    
    # Verifica se há estoque suficiente
    if medicamento.quantidade < quantidade_ofertada:
        flash(f"Estoque insuficiente. Disponível: {medicamento.quantidade}", "danger")
        return redirect(url_for("oferta_medicamento.listar_ofertas"))
    
    # Processa data de expiração se fornecida
    data_expiracao_dt = None
    if data_expiracao:
        from datetime import datetime
        try:
            data_expiracao_dt = datetime.strptime(data_expiracao, "%Y-%m-%d")
        except ValueError:
            flash("Data de expiração inválida.", "danger")
            return redirect(url_for("oferta_medicamento.listar_ofertas"))
    
    try:
        oferta = OfertaMedicamento(
            farmacia_id=farmacia_id,
            medicamento_id=medicamento_id,
            quantidade_ofertada=quantidade_ofertada,
            quantidade_reservada=0,
            status=StatusOferta.DISPONIVEL.value,
            data_expiracao=data_expiracao_dt,
            criado_por_id=1,  # TODO: Usar current_user.id quando autenticado
            observacoes=observacoes if observacoes else None
        )
        db.session.add(oferta)
        db.session.commit()
        registrar_log(
            "Criação Oferta Medicamento",
            f'Oferta criada: {medicamento.nome} - {quantidade_ofertada} unidades pela farmácia {farmacia.nome_fantasia}',
        )
        flash(f"Oferta de {medicamento.nome} criada com sucesso.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao criar oferta. Tente novamente.", "danger")
    
    return redirect(url_for("oferta_medicamento.listar_ofertas"))


@oferta_medicamento_bp.route("/<int:oid>/cancelar", methods=["POST"])
@login_required
@admin_required
def cancelar_oferta(oid):
    """Cancela uma oferta."""
    oferta = db.session.get(OfertaMedicamento, oid)
    if not oferta:
        flash("Oferta não encontrada.", "danger")
        return redirect(url_for("oferta_medicamento.listar_ofertas"))
    
    try:
        if oferta.cancelar():
            db.session.commit()
            registrar_log(
                "Cancelamento Oferta Medicamento",
                f'Oferta {oferta.id} cancelada',
            )
            flash(f"Oferta {oferta.id} cancelada com sucesso.", "success")
        else:
            flash("Não é possível cancelar esta oferta.", "danger")
    except Exception:
        db.session.rollback()
        flash("Erro ao cancelar oferta. Tente novamente.", "danger")
    
    return redirect(url_for("oferta_medicamento.listar_ofertas"))


@oferta_medicamento_bp.route("/<int:oid>/expirar", methods=["POST"])
@login_required
@admin_required
def expirar_oferta(oid):
    """Expira uma oferta manualmente."""
    oferta = db.session.get(OfertaMedicamento, oid)
    if not oferta:
        flash("Oferta não encontrada.", "danger")
        return redirect(url_for("oferta_medicamento.listar_ofertas"))
    
    try:
        if oferta.expirar():
            db.session.commit()
            registrar_log(
                "Expiração Oferta Medicamento",
                f'Oferta {oferta.id} expirada',
            )
            flash(f"Oferta {oferta.id} expirada com sucesso.", "success")
        else:
            flash("Não é possível expirar esta oferta.", "danger")
    except Exception:
        db.session.rollback()
        flash("Erro ao expirar oferta. Tente novamente.", "danger")
    
    return redirect(url_for("oferta_medicamento.listar_ofertas"))
