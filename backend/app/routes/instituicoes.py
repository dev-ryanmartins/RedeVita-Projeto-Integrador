from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.instituicao import Instituicao
from app.database import db
from app.core.decorators import admin_required
from app.utils.log_helper import registrar_log
from app.utils.sanitize import limpar
from app.utils.document_validation import validar_cnpj


instituicoes_bp = Blueprint("inst_mgmt", __name__, url_prefix="/instituicoes")


@instituicoes_bp.route("/")
@login_required
@admin_required
def listar_instituicoes():
    """Lista todas as instituições."""
    instituicoes = Instituicao.query.order_by(Instituicao.id).all()
    return render_template("instituicoes.html", instituicoes=instituicoes)


@instituicoes_bp.route("/cadastrar", methods=["POST"])
@login_required
@admin_required
def cadastrar_instituicao():
    """Cadastra uma nova instituição."""
    nome = limpar(request.form.get("nome", ""))
    cnpj = limpar(request.form.get("cnpj", ""))
    endereco = limpar(request.form.get("endereco", ""))
    responsavel = limpar(request.form.get("responsavel", ""))
    telefone = limpar(request.form.get("telefone", ""))
    email = limpar(request.form.get("email", ""))

    if not nome:
        flash("Nome da instituição é obrigatório.", "danger")
        return redirect(url_for("instituicoes.listar_instituicoes"))

    # Valida CNPJ se fornecido
    if cnpj and not validar_cnpj(cnpj):
        flash("CNPJ inválido.", "danger")
        return redirect(url_for("instituicoes.listar_instituicoes"))

    # Verifica duplicidade de CNPJ
    if cnpj:
        existente = Instituicao.query.filter_by(cnpj=cnpj).first()
        if existente:
            flash("Já existe uma instituição com este CNPJ.", "danger")
            return redirect(url_for("instituicoes.listar_instituicoes"))

    try:
        instituicao = Instituicao(
            nome=nome,
            cnpj=cnpj if cnpj else None,
            endereco=endereco if endereco else None,
            responsavel=responsavel if responsavel else None,
            telefone=telefone if telefone else None,
            email=email if email else None,
            ativo=True
        )
        db.session.add(instituicao)
        db.session.commit()
        registrar_log(
            "Cadastro Instituição",
            f'Instituição "{nome}" cadastrada',
        )
        flash(f"Instituição {nome} cadastrada com sucesso.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao cadastrar instituição. Tente novamente.", "danger")

    return redirect(url_for("instituicoes.listar_instituicoes"))


@instituicoes_bp.route("/<int:pid>/editar", methods=["POST"])
@login_required
@admin_required
def editar_instituicao(pid):
    """Edita uma instituição."""
    instituicao = db.session.get(Instituicao, pid)
    if not instituicao:
        flash("Instituição não encontrada.", "danger")
        return redirect(url_for("instituicoes.listar_instituicoes"))

    nome = limpar(request.form.get("nome", ""))
    cnpj = limpar(request.form.get("cnpj", ""))
    endereco = limpar(request.form.get("endereco", ""))
    responsavel = limpar(request.form.get("responsavel", ""))
    telefone = limpar(request.form.get("telefone", ""))
    email = limpar(request.form.get("email", ""))

    if not nome:
        flash("Nome da instituição é obrigatório.", "danger")
        return redirect(url_for("instituicoes.listar_instituicoes"))

    # Valida CNPJ se fornecido
    if cnpj and not validar_cnpj(cnpj):
        flash("CNPJ inválido.", "danger")
        return redirect(url_for("instituicoes.listar_instituicoes"))

    # Verifica duplicidade de CNPJ (exceto a própria instituição)
    if cnpj:
        existente = Instituicao.query.filter(
            Instituicao.cnpj == cnpj,
            Instituicao.id != pid
        ).first()
        if existente:
            flash("Já existe uma instituição com este CNPJ.", "danger")
            return redirect(url_for("instituicoes.listar_instituicoes"))

    try:
        instituicao.nome = nome
        instituicao.cnpj = cnpj if cnpj else None
        instituicao.endereco = endereco if endereco else None
        instituicao.responsavel = responsavel if responsavel else None
        instituicao.telefone = telefone if telefone else None
        instituicao.email = email if email else None
        db.session.commit()
        registrar_log(
            "Edição Instituição",
            f'Instituição "{nome}" editada',
        )
        flash(f"Instituição {nome} atualizada com sucesso.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao atualizar instituição. Tente novamente.", "danger")

    return redirect(url_for("instituicoes.listar_instituicoes"))


@instituicoes_bp.route("/<int:pid>/toggle-ativo", methods=["POST"])
@login_required
@admin_required
def toggle_ativo(pid):
    """Ativa ou desativa uma instituição."""
    instituicao = db.session.get(Instituicao, pid)
    if not instituicao:
        flash("Instituição não encontrada.", "danger")
        return redirect(url_for("instituicoes.listar_instituicoes"))

    try:
        instituicao.ativo = not instituicao.ativo
        db.session.commit()
        status = "ativada" if instituicao.ativo else "desativada"
        registrar_log(
            "Alteração Status Instituição",
            f'Instituição "{instituicao.nome}" {status}',
        )
        flash(f"Instituição {instituicao.nome} {status}.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao alterar status da instituição. Tente novamente.", "danger")

    return redirect(url_for("instituicoes.listar_instituicoes"))
