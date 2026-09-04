from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.receita import Receita
from app.models.paciente import Paciente
from app.models.medico import Medico
from app.models.medicamento import Medicamento
from app.database import db
from app.core.decorators import cargo_required
from app.utils.log_helper import registrar_log

medical_bp = Blueprint("medical", __name__, url_prefix="/medical")

TIPOS_RECEITA = [
    "Receita Simples",
    "Receita de Controle Especial (Branca)",
    "Receita 'B' Especial (Azul)",
    "Receita 'A' (Amarela)",
]


@medical_bp.route("/prescriptions")
@login_required
@cargo_required("Admin", "Médico")
def prescriptions():
    receitas = Receita.query.order_by(Receita.data_emissao.desc()).all()
    pacientes = Paciente.query.order_by(Paciente.nome).all()
    medicos = Medico.query.order_by(Medico.nome).all()
    medicamentos = (
        Medicamento.query.filter(Medicamento.quantidade > 0)
        .order_by(Medicamento.nome)
        .all()
    )
    total_pendentes = sum(1 for r in receitas if r.status == "pendente")
    total_controladas = sum(
        1 for r in receitas if r.medicamento and r.medicamento.controlado
    )
    return render_template(
        "medical_prescriptions.html",
        receitas=receitas,
        pacientes=pacientes,
        medicos=medicos,
        medicamentos=medicamentos,
        tipos_receita=TIPOS_RECEITA,
        total_pendentes=total_pendentes,
        total_controladas=total_controladas,
    )


@medical_bp.route("/prescriptions/nova", methods=["POST"])
@login_required
@cargo_required("Admin", "Médico")
def nova_prescricao():
    paciente_id = request.form.get("paciente_id", type=int)
    medico_id = request.form.get("medico_id", type=int)
    medicamento_id = request.form.get("medicamento_id", type=int) or None
    observacoes = request.form.get("observacoes", "").strip()
    tipo_receita = request.form.get("tipo_receita", "").strip() or None

    if not paciente_id or not medico_id:
        flash("Selecione o paciente e o médico.", "danger")
        return redirect(url_for("medical.prescriptions"))

    paciente = db.session.get(Paciente, paciente_id)
    medico = db.session.get(Medico, medico_id)
    if not paciente or not medico:
        flash("Paciente ou médico não encontrado.", "danger")
        return redirect(url_for("medical.prescriptions"))

    if medicamento_id:
        med = db.session.get(Medicamento, medicamento_id)
        if med and med.controlado and not tipo_receita:
            flash(
                f'"{med.nome}" é um medicamento controlado (Portaria 344). '
                "O tipo de receita especial é obrigatório.",
                "danger",
            )
            return redirect(url_for("medical.prescriptions"))

    try:
        receita = Receita(
            paciente_id=paciente_id,
            medico_id=medico_id,
            medicamento_id=medicamento_id,
            observacoes=observacoes or None,
            tipo_receita=tipo_receita,
            status="pendente",
        )
        db.session.add(receita)
        db.session.commit()

        med_nome = ""
        if medicamento_id:
            m = db.session.get(Medicamento, medicamento_id)
            med_nome = f" — {m.nome}" if m else ""
            if m and m.controlado:
                registrar_log(
                    "Portaria 344 - Prescrição Digital",
                    f'Receita CONTROLADA emitida por Dr(a). "{medico.nome}" (CRM: {medico.crm}) '
                    f'para "{paciente.nome}"{med_nome} | Tipo: {tipo_receita}',
                )
            else:
                registrar_log(
                    "Prescrição Digital",
                    f'Receita emitida por Dr(a). "{medico.nome}" para "{paciente.nome}"{med_nome}',
                )
        else:
            registrar_log(
                "Prescrição Digital",
                f'Receita emitida por Dr(a). "{medico.nome}" para "{paciente.nome}"',
            )

        flash("Prescrição emitida com sucesso!", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao emitir prescrição. Tente novamente.", "danger")

    return redirect(url_for("medical.prescriptions"))
