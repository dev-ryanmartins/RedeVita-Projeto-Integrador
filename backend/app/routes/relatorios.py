import csv
import io
from flask import Blueprint, render_template, request, Response, redirect, url_for
from flask_login import login_required
from app.core.decorators import equipe_clinica_required
from app.models.medicamento import Medicamento
from app.models.medico import Medico
from app.models.farmacia import Farmacia
from app.models.doacao import Doacao
from app.models.paciente import Paciente
from app.utils.log_helper import registrar_log
from datetime import date, timedelta

relatorios_bp = Blueprint('relatorios', __name__)


@relatorios_bp.route('/relatorios')
@login_required
@equipe_clinica_required
def relatorios():
    hoje = date.today()

    proximos_vencimento = (
        Medicamento.query
        .filter(Medicamento.status_semaforo == 1)
        .order_by(Medicamento.data_validade)
        .all()
    )
    vencidos = (
        Medicamento.query
        .filter(Medicamento.status_semaforo == 2)
        .order_by(Medicamento.data_validade)
        .all()
    )

    total_medicos = Medico.query.count()
    total_farmacias = Farmacia.query.count()
    total_medicamentos = Medicamento.query.count()
    total_doacoes = Doacao.query.count()
    total_pacientes = Paciente.query.count()

    return render_template(
        'relatorios.html',
        proximos_vencimento=proximos_vencimento,
        vencidos=vencidos,
        total_medicos=total_medicos,
        total_farmacias=total_farmacias,
        total_medicamentos=total_medicamentos,
        total_doacoes=total_doacoes,
        total_pacientes=total_pacientes,
        hoje=hoje
    )


def _make_csv_response(filename: str, headers: list, rows: list) -> Response:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    output.seek(0)
    bom = '\ufeff'
    return Response(
        bom + output.getvalue(),
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@relatorios_bp.route('/relatorios/exportar/medicos')
@login_required
@equipe_clinica_required
def exportar_medicos():
    medicos = Medico.query.order_by(Medico.nome).all()
    registrar_log('Exportação CSV', 'Exportou lista de médicos')
    rows = [
        [m.id, m.nome, m.crm, m.especialidade, m.contato or '',
         m.created_at.strftime('%d/%m/%Y') if m.created_at else '']
        for m in medicos
    ]
    return _make_csv_response(
        f'medicos_{date.today()}.csv',
        ['ID', 'Nome', 'CRM', 'Especialidade', 'Contato', 'Cadastrado em'],
        rows
    )


@relatorios_bp.route('/relatorios/exportar/farmacias')
@login_required
@equipe_clinica_required
def exportar_farmacias():
    farmacias = Farmacia.query.order_by(Farmacia.nome_fantasia).all()
    registrar_log('Exportação CSV', 'Exportou lista de farmácias')
    rows = [
        [f.id, f.nome_fantasia, f.razao_social or '', f.cnpj, f.responsavel, f.endereco,
         f.created_at.strftime('%d/%m/%Y') if f.created_at else '']
        for f in farmacias
    ]
    return _make_csv_response(
        f'farmacias_{date.today()}.csv',
        ['ID', 'Nome Fantasia', 'Razão Social', 'CNPJ', 'Responsável', 'Endereço', 'Cadastrado em'],
        rows
    )


@relatorios_bp.route('/relatorios/exportar/medicamentos')
@login_required
@equipe_clinica_required
def exportar_medicamentos():
    medicamentos = Medicamento.query.order_by(Medicamento.nome).all()
    registrar_log('Exportação CSV', 'Exportou lista de medicamentos')
    status_map = {0: 'Seguro', 1: 'Próximo Vencimento', 2: 'Vencido'}
    rows = [
        [m.id, m.nome, m.lote, m.data_validade.strftime('%d/%m/%Y'),
         m.quantidade, status_map.get(m.status_semaforo, '')]
        for m in medicamentos
    ]
    return _make_csv_response(
        f'medicamentos_{date.today()}.csv',
        ['ID', 'Nome', 'Lote', 'Validade', 'Quantidade', 'Status'],
        rows
    )


@relatorios_bp.route('/relatorios/exportar/pacientes')
@login_required
@equipe_clinica_required
def exportar_pacientes():
    pacientes = Paciente.query.order_by(Paciente.nome).all()
    registrar_log('Exportação CSV', 'Exportou lista de pacientes')
    rows = [
        [p.id, p.nome, p.cpf,
         p.data_nascimento.strftime('%d/%m/%Y') if p.data_nascimento else '',
         p.endereco or '',
         p.created_at.strftime('%d/%m/%Y') if p.created_at else '']
        for p in pacientes
    ]
    return _make_csv_response(
        f'pacientes_{date.today()}.csv',
        ['ID', 'Nome', 'CPF', 'Data de Nascimento', 'Endereço', 'Cadastrado em'],
        rows
    )
