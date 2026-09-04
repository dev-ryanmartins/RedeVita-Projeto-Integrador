from flask import Blueprint, render_template
from flask_login import login_required
from app.models.medicamento import Medicamento
from app.core.decorators import cargo_required
from datetime import date

pharmacy_bp = Blueprint("pharmacy", __name__, url_prefix="/pharmacy")


def _dados_auditoria():
    hoje = date.today()
    vencidos = (
        Medicamento.query.filter(Medicamento.status_semaforo == 2)
        .order_by(Medicamento.data_validade)
        .all()
    )
    proximos = (
        Medicamento.query.filter(Medicamento.status_semaforo == 1)
        .order_by(Medicamento.data_validade)
        .all()
    )
    controlados_criticos = [m for m in vencidos + proximos if m.controlado]
    total_unidades_vencidas = sum(m.quantidade for m in vencidos)
    return dict(
        vencidos=vencidos,
        proximos=proximos,
        controlados_criticos=controlados_criticos,
        total_unidades_vencidas=total_unidades_vencidas,
        hoje=hoje,
    )


@pharmacy_bp.route("/auditoria")
@login_required
@cargo_required("Admin", "Farmacêutico", "Operador")
def auditoria():
    return render_template("auditoria.html", **_dados_auditoria())


@pharmacy_bp.route("/audit")
@login_required
@cargo_required("Admin", "Farmacêutico")
def audit():
    return render_template("pharmacy_audit.html", **_dados_auditoria())
