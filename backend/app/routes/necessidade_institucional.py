"""
Rotas para Quadro Privado de Necessidades de Instituições

NOTA: Funcionalidade Admin-only devido à ausência de vínculo confiável
entre usuários e instituições/farmácias no modelo atual.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.database import db
from app.core.decorators import admin_required
from app.models.necessidade_institucional import NecessidadeInstitucional, StatusNecessidade, PrioridadeNecessidade
from app.models.usuario import Usuario
from app.models.medicamento_referencia import MedicamentoReferencia
from datetime import datetime

necessidade_institucional_bp = Blueprint("necessidade_institucional", __name__)


@necessidade_institucional_bp.route("/necessidades-institucionais", methods=["GET", "POST"])
@login_required
@admin_required
def listar_necessidades():
    """Lista todas as necessidades institucionais."""
    if request.method == "POST":
        # Criar nova necessidade
        nome_instituicao = request.form.get("nome_instituicao", "").strip()
        medicamento_referencia_id = request.form.get("medicamento_referencia_id", type=int) or None
        produto_descritivo = request.form.get("produto_descritivo", "").strip()
        quantidade_solicitada = request.form.get("quantidade_solicitada", type=int)
        unidade = request.form.get("unidade", "unidade").strip()
        data_desejada_str = request.form.get("data_desejada", "").strip()
        prioridade = request.form.get("prioridade", PrioridadeNecessidade.MEDIA.value).strip()
        observacoes = request.form.get("observacoes", "").strip() or None
        
        # Validações básicas
        if not nome_instituicao:
            flash("Nome da instituição é obrigatório.", "danger")
            return redirect(url_for("necessidade_institucional.listar_necessidades"))
        
        if not produto_descritivo and not medicamento_referencia_id:
            flash("Informe o produto (referência ou descritivo).", "danger")
            return redirect(url_for("necessidade_institucional.listar_necessidades"))
        
        if not quantidade_solicitada or quantidade_solicitada <= 0:
            flash("Quantidade deve ser maior que zero.", "danger")
            return redirect(url_for("necessidade_institucional.listar_necessidades"))
        
        # Parse data
        data_desejada = None
        if data_desejada_str:
            try:
                data_desejada = datetime.strptime(data_desejada_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Data desejada inválida. Use formato AAAA-MM-DD.", "danger")
                return redirect(url_for("necessidade_institucional.listar_necessidades"))
        
        try:
            necessidade = NecessidadeInstitucional(
                nome_instituicao=nome_instituicao,
                medicamento_referencia_id=medicamento_referencia_id,
                produto_descritivo=produto_descritivo,
                quantidade_solicitada=quantidade_solicitada,
                unidade=unidade,
                data_desejada=data_desejada,
                prioridade=prioridade,
                status=StatusNecessidade.RASCUNHO.value,
                criado_por_id=current_user.id,
                observacoes=observacoes
            )
            db.session.add(necessidade)
            db.session.commit()
            flash("Necessidade registrada com sucesso.", "success")
        except Exception:
            db.session.rollback()
            flash("Erro ao registrar necessidade. Tente novamente.", "danger")
        
        return redirect(url_for("necessidade_institucional.listar_necessidades"))
    
    # Filtros
    status_filtro = request.args.get("status", "").strip()
    prioridade_filtro = request.args.get("prioridade", "").strip()
    
    query = NecessidadeInstitucional.query
    
    if status_filtro:
        query = query.filter(NecessidadeInstitucional.status == status_filtro)
    
    if prioridade_filtro:
        query = query.filter(NecessidadeInstitucional.prioridade == prioridade_filtro)
    
    necessidades = query.order_by(NecessidadeInstitucional.criado_em.desc()).all()
    referencias = MedicamentoReferencia.query.all()
    
    return render_template(
        "necessidades_institucionais.html",
        necessidades=necessidades,
        referencias=referencias,
        status_filtro=status_filtro,
        prioridade_filtro=prioridade_filtro
    )


@necessidade_institucional_bp.route("/necessidades-institucionais/<int:id>/revisar", methods=["POST"])
@login_required
@admin_required
def revisar_necessidade(id):
    """Revisar uma necessidade."""
    necessidade = NecessidadeInstitucional.query.get_or_404(id)
    
    novo_status = request.form.get("status").strip()
    
    if novo_status not in [s.value for s in StatusNecessidade]:
        flash("Status inválido.", "danger")
        return redirect(url_for("necessidade_institucional.listar_necessidades"))
    
    try:
        necessidade.status = novo_status
        necessidade.revisado_por_id = current_user.id
        necessidade.revisado_em = datetime.utcnow()
        db.session.commit()
        flash("Necessidade revisada com sucesso.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao revisar necessidade. Tente novamente.", "danger")
    
    return redirect(url_for("necessidade_institucional.listar_necessidades"))


@necessidade_institucional_bp.route("/necessidades-institucionais/<int:id>/encerrar", methods=["POST"])
@login_required
@admin_required
def encerrar_necessidade(id):
    """Encerrar uma necessidade."""
    necessidade = NecessidadeInstitucional.query.get_or_404(id)
    
    try:
        necessidade.status = StatusNecessidade.ENCERRADA.value
        necessidade.encerrado_por_id = current_user.id
        necessidade.encerrado_em = datetime.utcnow()
        db.session.commit()
        flash("Necessidade encerrada com sucesso.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao encerrar necessidade. Tente novamente.", "danger")
    
    return redirect(url_for("necessidade_institucional.listar_necessidades"))


@necessidade_institucional_bp.route("/necessidades-institucionais/<int:id>/detalhes")
@login_required
@admin_required
def detalhes_necessidade(id):
    """Detalhes de uma necessidade."""
    necessidade = NecessidadeInstitucional.query.get_or_404(id)
    return render_template("necessidade_detalhes.html", necessidade=necessidade)
