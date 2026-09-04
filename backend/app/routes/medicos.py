import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.medico import Medico
from app.database import db
from app.core.decorators import (
    admin_required,
    operador_required,
    equipe_clinica_required,
)
from app.utils.log_helper import registrar_log

medicos_bp = Blueprint("medicos", __name__)

_MAX_NOME = 150
_MAX_CRM = 20
_MAX_ESPEC = 100
_MAX_CONTATO = 20


def _limpar_tel(tel: str) -> str:
    digits = re.sub(r"\D", "", tel)
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return tel.strip()


def _validar_campos_medico(nome, crm, especialidade, contato_raw):
    if not nome or not crm or not especialidade:
        return "Preencha todos os campos obrigatórios."
    if len(nome) > _MAX_NOME:
        return f"Nome muito longo (máx. {_MAX_NOME} caracteres)."
    if len(crm) > _MAX_CRM:
        return f"CRM inválido (máx. {_MAX_CRM} caracteres)."
    if len(especialidade) > _MAX_ESPEC:
        return f"Especialidade muito longa (máx. {_MAX_ESPEC} caracteres)."
    digits_contato = re.sub(r"\D", "", contato_raw)
    if contato_raw and len(digits_contato) > _MAX_CONTATO:
        return "Número de contato inválido."
    return None


@medicos_bp.route("/medicos")
@login_required
@equipe_clinica_required
def listar_medicos():
    try:
        medicos = Medico.query.order_by(Medico.id.desc()).all()
    except Exception:
        medicos = []
    return render_template("medicos.html", medicos=medicos)


@medicos_bp.route("/medico/novo", methods=["POST"])
@login_required
@operador_required
def novo_medico():
    nome = request.form.get("nome", "").strip()[:_MAX_NOME]
    crm = request.form.get("crm", "").strip()[:_MAX_CRM]
    especialidade = request.form.get("especialidade", "").strip()[:_MAX_ESPEC]
    contato_raw = request.form.get("contato", "").strip()[: _MAX_CONTATO + 5]
    contato = _limpar_tel(contato_raw) if contato_raw else None

    erro = _validar_campos_medico(nome, crm, especialidade, contato_raw)
    if erro:
        flash(erro, "danger")
        return redirect(url_for("medicos.listar_medicos"))

    if Medico.query.filter_by(crm=crm).first():
        flash(f'CRM "{crm}" já está cadastrado no sistema.', "danger")
        return redirect(url_for("medicos.listar_medicos"))

    try:
        medico = Medico(
            nome=nome, crm=crm, especialidade=especialidade, contato=contato
        )
        db.session.add(medico)
        db.session.commit()
        registrar_log("Novo Médico", f'Médico "{nome}" ({crm}) cadastrado')
        flash(f'Médico "{nome}" cadastrado com sucesso!', "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao cadastrar médico. Tente novamente.", "danger")

    return redirect(url_for("medicos.listar_medicos"))


@medicos_bp.route("/medico/<int:medico_id>/editar", methods=["POST"])
@login_required
@operador_required
def editar_medico(medico_id):
    medico = db.session.get(Medico, medico_id)
    if not medico:
        flash("Médico não encontrado.", "danger")
        return redirect(url_for("medicos.listar_medicos"))

    nome = request.form.get("nome", "").strip()[:_MAX_NOME]
    crm = request.form.get("crm", "").strip()[:_MAX_CRM]
    especialidade = request.form.get("especialidade", "").strip()[:_MAX_ESPEC]
    contato_raw = request.form.get("contato", "").strip()[: _MAX_CONTATO + 5]
    contato = _limpar_tel(contato_raw) if contato_raw else None

    erro = _validar_campos_medico(nome, crm, especialidade, contato_raw)
    if erro:
        flash(erro, "danger")
        return redirect(url_for("medicos.listar_medicos"))

    existente = Medico.query.filter_by(crm=crm).first()
    if existente and existente.id != medico_id:
        flash(f'CRM "{crm}" já pertence a outro médico cadastrado.', "danger")
        return redirect(url_for("medicos.listar_medicos"))

    try:
        medico.nome = nome
        medico.crm = crm
        medico.especialidade = especialidade
        medico.contato = contato
        db.session.commit()
        registrar_log("Edição de Médico", f'Dados do médico "{nome}" atualizados')
        flash(f'Dados do Dr(a). "{nome}" atualizados com sucesso!', "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao atualizar médico. Tente novamente.", "danger")

    return redirect(url_for("medicos.listar_medicos"))


@medicos_bp.route("/medico/<int:medico_id>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir_medico(medico_id):
    medico = db.session.get(Medico, medico_id)
    if not medico:
        flash("Médico não encontrado.", "danger")
        return redirect(url_for("medicos.listar_medicos"))

    nome = medico.nome
    try:
        db.session.delete(medico)
        db.session.commit()
        registrar_log("Exclusão de Médico", f'Médico "{nome}" removido do sistema')
        flash(f'Médico "{nome}" removido com sucesso.', "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao remover médico. Tente novamente.", "danger")

    return redirect(url_for("medicos.listar_medicos"))
