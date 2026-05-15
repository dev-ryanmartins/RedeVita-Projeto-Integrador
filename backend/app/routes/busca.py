from flask import Blueprint, render_template, request
from flask_login import login_required
from app.models.medicamento import Medicamento
from app.models.paciente import Paciente
from app.models.medico import Medico
from app.models.farmacia import Farmacia

busca_bp = Blueprint('busca', __name__)


@busca_bp.route('/buscar')
@login_required
def buscar():
    q = request.args.get('q', '').strip()
    medicamentos = []
    pacientes = []
    medicos = []
    farmacias = []

    if len(q) >= 2:
        like = f'%{q}%'
        medicamentos = Medicamento.query.filter(
            Medicamento.nome.ilike(like) | Medicamento.principio_ativo.ilike(like)
        ).limit(20).all()
        pacientes = Paciente.query.filter(
            Paciente.nome.ilike(like) | Paciente.cpf.ilike(like)
        ).limit(20).all()
        medicos = Medico.query.filter(
            Medico.nome.ilike(like) | Medico.crm.ilike(like)
        ).limit(20).all()
        farmacias = Farmacia.query.filter(
            Farmacia.nome_fantasia.ilike(like)
        ).limit(20).all()

    total = len(medicamentos) + len(pacientes) + len(medicos) + len(farmacias)
    return render_template(
        'busca.html',
        q=q,
        medicamentos=medicamentos,
        pacientes=pacientes,
        medicos=medicos,
        farmacias=farmacias,
        total=total,
    )
