import io
import re
import csv
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, jsonify
from flask_login import login_required
from app.models.medicamento import Medicamento
from app.models.medicamento_referencia import MedicamentoReferencia
from app.models.doacao import Doacao
from app.models.medico import Medico
from app.models.farmacia import Farmacia
from app.models.paciente import Paciente
from app.database import db
from app.utils.semaforo import calcular_status_semaforo
from app.schemas.med_schema import validar_entrada_medicamento
from app.utils.log_helper import registrar_log
from app.core.decorators import admin_required, farmaceutico_required
from datetime import datetime, date

inventory_bp = Blueprint('inventory', __name__)

TARJAS_VALIDAS = ['Sem Tarja', 'Tarja Amarela', 'Tarja Vermelha', 'Portaria 344']
TIPOS_RECEITA = [
    'Receita Simples',
    'Receita de Controle Especial (Branca)',
    "Receita 'B' Especial (Azul)",
    "Receita 'A' (Amarela)",
]


# ── API: busca na tabela de referência ANVISA ────────────────────────────────

@inventory_bp.route('/api/referencia/buscar')
@login_required
def buscar_referencia():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify([])
    resultados = (
        MedicamentoReferencia.query
        .filter(MedicamentoReferencia.nome_comercial.ilike(f'%{q}%'))
        .order_by(MedicamentoReferencia.nome_comercial)
        .limit(10)
        .all()
    )
    return jsonify([r.to_dict() for r in resultados])


# ── Dashboard ────────────────────────────────────────────────────────────────

@inventory_bp.route('/dashboard')
@login_required
def dashboard():
    medicamentos = Medicamento.query.all()
    total_itens = len(medicamentos)
    total_estoque = sum(m.quantidade for m in medicamentos)
    alertas = len([m for m in medicamentos if m.status_semaforo == 2])
    sem_estoque = len([m for m in medicamentos if m.quantidade == 0])
    total_doacoes = Doacao.query.count()
    total_medicos = Medico.query.count()
    total_farmacias = Farmacia.query.count()
    total_pacientes = Paciente.query.count()

    proximos_vencimento = (
        Medicamento.query
        .filter(Medicamento.status_semaforo == 1)
        .order_by(Medicamento.data_validade)
        .limit(5)
        .all()
    )
    ultimos_medicamentos = Medicamento.query.order_by(Medicamento.id.desc()).limit(5).all()
    ultimos_medicos = Medico.query.order_by(Medico.id.desc()).limit(3).all()
    ultimas_farmacias = Farmacia.query.order_by(Farmacia.id.desc()).limit(3).all()

    return render_template(
        'dashboard.html',
        total=total_itens,
        estoque=total_estoque,
        alertas=alertas,
        total_doacoes=total_doacoes,
        total_medicos=total_medicos,
        total_farmacias=total_farmacias,
        total_pacientes=total_pacientes,
        medicamentos=ultimos_medicamentos,
        proximos_vencimento=proximos_vencimento,
        ultimos_medicos=ultimos_medicos,
        ultimas_farmacias=ultimas_farmacias,
        sem_estoque=sem_estoque,
        now=date.today()
    )


# ── Inventário ───────────────────────────────────────────────────────────────

@inventory_bp.route('/inventario')
@login_required
def listar_medicamentos():
    medicamentos = Medicamento.query.order_by(Medicamento.id.desc()).all()
    referencias = MedicamentoReferencia.query.order_by(MedicamentoReferencia.nome_comercial).all()
    total_controlados = sum(1 for m in medicamentos if m.controlado)
    total_continuo = sum(1 for m in medicamentos if m.uso_continuo)
    return render_template(
        'inventario.html',
        medicamentos=medicamentos,
        referencias=referencias,
        total_controlados=total_controlados,
        total_continuo=total_continuo,
        tarjas=TARJAS_VALIDAS,
        tipos_receita=TIPOS_RECEITA,
    )


# ── Exportar CSV ─────────────────────────────────────────────────────────────

@inventory_bp.route('/inventario/exportar-csv')
@login_required
@farmaceutico_required
def exportar_csv():
    medicamentos = Medicamento.query.order_by(Medicamento.nome).all()
    status_map = {0: 'Seguro', 1: 'Atenção', 2: 'Vencido'}

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
    writer.writerow(['Nome', 'Princípio Ativo', 'Tarja', 'Lote', 'Validade', 'Quantidade', 'Status', 'Uso Contínuo'])
    for med in medicamentos:
        writer.writerow([
            med.nome,
            med.principio_ativo or '—',
            med.tarja,
            med.lote,
            med.data_validade.strftime('%d/%m/%Y'),
            med.quantidade,
            status_map.get(med.status_semaforo, '—'),
            'Sim' if med.uso_continuo else 'Não',
        ])

    registrar_log('Exportação CSV', f'Estoque exportado ({len(medicamentos)} medicamentos)')

    filename = f'estoque_redevita_{date.today().strftime("%Y%m%d")}.csv'
    return Response(
        '\ufeff' + output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


# ── Novo Medicamento ─────────────────────────────────────────────────────────

@inventory_bp.route('/medicamento/novo', methods=['POST'])
@login_required
@farmaceutico_required
def novo_medicamento():
    dados = {
        'nome':          request.form.get('nome', '').strip(),
        'lote':          request.form.get('lote', '').strip(),
        'data_validade': request.form.get('data_validade', '').strip(),
        'quantidade':    request.form.get('quantidade', '').strip(),
    }

    valido, erros = validar_entrada_medicamento(dados)
    if not valido:
        for erro in erros:
            flash(erro, 'danger')
        return redirect(url_for('inventory.listar_medicamentos'))

    tarja = request.form.get('tarja', 'Sem Tarja').strip()
    if tarja not in TARJAS_VALIDAS:
        tarja = 'Sem Tarja'

    principio_ativo = request.form.get('principio_ativo', '').strip() or None
    uso_continuo = request.form.get('uso_continuo') == '1'
    registro_ms = request.form.get('registro_ms', '').strip() or None
    referencia_id = request.form.get('referencia_id', type=int) or None

    try:
        data_dt = datetime.strptime(dados['data_validade'], '%Y-%m-%d').date()
        status = calcular_status_semaforo(data_dt)
        novo_med = Medicamento(
            nome=dados['nome'],
            lote=dados['lote'],
            data_validade=data_dt,
            quantidade=int(dados['quantidade']),
            status_semaforo=status,
            tarja=tarja,
            principio_ativo=principio_ativo,
            uso_continuo=uso_continuo,
            referencia_id=referencia_id,
        )
        db.session.add(novo_med)
        db.session.commit()

        acao = 'Portaria 344 - Cadastro' if tarja == 'Portaria 344' else 'Novo Medicamento'
        registrar_log(acao, f'Medicamento "{dados["nome"]}" (Tarja: {tarja}, Lote: {dados["lote"]}) cadastrado')
        flash('Medicamento cadastrado com sucesso!', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao cadastrar medicamento. Tente novamente.', 'danger')

    return redirect(url_for('inventory.listar_medicamentos'))


# ── Editar Medicamento ────────────────────────────────────────────────────────

@inventory_bp.route('/medicamento/<int:med_id>/editar', methods=['POST'])
@login_required
@farmaceutico_required
def editar_medicamento(med_id):
    med = db.session.get(Medicamento, med_id)
    if not med:
        flash('Medicamento não encontrado.', 'danger')
        return redirect(url_for('inventory.listar_medicamentos'))

    dados = {
        'nome':          request.form.get('nome', '').strip(),
        'lote':          request.form.get('lote', '').strip(),
        'data_validade': request.form.get('data_validade', '').strip(),
        'quantidade':    request.form.get('quantidade', '').strip(),
    }

    valido, erros = validar_entrada_medicamento(dados)
    if not valido:
        for erro in erros:
            flash(erro, 'danger')
        return redirect(url_for('inventory.listar_medicamentos'))

    tarja = request.form.get('tarja', med.tarja).strip()
    if tarja not in TARJAS_VALIDAS:
        tarja = med.tarja

    principio_ativo = request.form.get('principio_ativo', '').strip() or None
    uso_continuo = request.form.get('uso_continuo') == '1'

    try:
        data_dt = datetime.strptime(dados['data_validade'], '%Y-%m-%d').date()
        med.nome = dados['nome']
        med.lote = dados['lote']
        med.data_validade = data_dt
        med.quantidade = int(dados['quantidade'])
        med.status_semaforo = calcular_status_semaforo(data_dt)
        med.tarja = tarja
        med.principio_ativo = principio_ativo
        med.uso_continuo = uso_continuo
        db.session.commit()

        acao = 'Portaria 344 - Edição' if tarja == 'Portaria 344' else 'Edição de Medicamento'
        registrar_log(acao, f'Medicamento "{med.nome}" (Tarja: {tarja}) atualizado')
        flash('Medicamento atualizado com sucesso!', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao atualizar medicamento. Tente novamente.', 'danger')

    return redirect(url_for('inventory.listar_medicamentos'))


# ── Baixar Estoque ────────────────────────────────────────────────────────────

@inventory_bp.route('/medicamento/<int:med_id>/baixar-estoque', methods=['POST'])
@login_required
@farmaceutico_required
def baixar_estoque(med_id):
    med = db.session.get(Medicamento, med_id)
    if not med:
        flash('Medicamento não encontrado.', 'danger')
        return redirect(url_for('inventory.listar_medicamentos'))

    quantidade = request.form.get('quantidade', type=int) or 0
    motivo = request.form.get('motivo', '').strip()

    if quantidade <= 0:
        flash('Informe uma quantidade válida (mínimo 1).', 'danger')
        return redirect(url_for('inventory.listar_medicamentos'))

    if quantidade > med.quantidade:
        flash(f'Estoque insuficiente. Disponível: {med.quantidade} un.', 'danger')
        return redirect(url_for('inventory.listar_medicamentos'))

    # ── Bloqueio para medicamentos controlados (Portaria 344) ────────────────
    if med.controlado:
        crm_raw = request.form.get('crm_medico', '').strip()
        tipo_receita = request.form.get('tipo_receita', '').strip()
        num_receita = request.form.get('numero_receita', '').strip()

        crm_digits = re.sub(r'\D', '', crm_raw)
        if len(crm_digits) < 4:
            flash(
                'Medicamento Portaria 344: CRM do médico é obrigatório e deve ter ao menos 4 dígitos.',
                'danger'
            )
            return redirect(url_for('inventory.listar_medicamentos'))

        if not tipo_receita or tipo_receita not in TIPOS_RECEITA:
            flash(
                'Medicamento Portaria 344: Tipo de receita controlada é obrigatório.',
                'danger'
            )
            return redirect(url_for('inventory.listar_medicamentos'))

    try:
        med.quantidade -= quantidade
        db.session.commit()

        detalhes = f'Baixa de {quantidade} un. de "{med.nome}" — Motivo: {motivo or "não informado"}'
        if med.controlado:
            detalhes += (
                f' | CRM: {crm_raw} | Receita: {tipo_receita}'
                + (f' | Nº {num_receita}' if num_receita else '')
            )

        acao = 'Portaria 344 - Movimentação' if med.controlado else 'Baixa de Estoque'
        registrar_log(acao, detalhes)
        flash(f'Baixa de {quantidade} un. de "{med.nome}" registrada com sucesso.', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao registrar a baixa. Tente novamente.', 'danger')

    return redirect(url_for('inventory.listar_medicamentos'))


# ── Excluir Medicamento ───────────────────────────────────────────────────────

@inventory_bp.route('/medicamento/<int:med_id>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_medicamento(med_id):
    med = db.session.get(Medicamento, med_id)
    if not med:
        flash('Medicamento não encontrado.', 'danger')
        return redirect(url_for('inventory.listar_medicamentos'))

    try:
        nome = med.nome
        tarja = med.tarja
        db.session.delete(med)
        db.session.commit()
        acao = 'Portaria 344 - Exclusão' if tarja == 'Portaria 344' else 'Exclusão de Medicamento'
        registrar_log(acao, f'Medicamento "{nome}" (Tarja: {tarja}) removido do sistema')
        flash(f'Medicamento "{nome}" removido com sucesso.', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao remover medicamento. Verifique se há doações vinculadas.', 'danger')

    return redirect(url_for('inventory.listar_medicamentos'))


# ── Duplicar Medicamento ──────────────────────────────────────────────────────

@inventory_bp.route('/medicamento/<int:med_id>/duplicar', methods=['POST'])
@login_required
@farmaceutico_required
def duplicar_medicamento(med_id):
    orig = db.session.get(Medicamento, med_id)
    if not orig:
        flash('Medicamento não encontrado.', 'danger')
        return redirect(url_for('inventory.listar_medicamentos'))
    try:
        copia = Medicamento(
            nome=orig.nome,
            lote=f'COPIA-{orig.lote}',
            data_validade=orig.data_validade,
            quantidade=0,
            status_semaforo=orig.status_semaforo,
            tarja=orig.tarja,
            principio_ativo=orig.principio_ativo,
            uso_continuo=orig.uso_continuo,
            referencia_id=orig.referencia_id,
        )
        db.session.add(copia)
        db.session.commit()
        registrar_log('Medicamento Duplicado', f'"{orig.nome}" (Lote {orig.lote}) duplicado com lote COPIA-{orig.lote}')
        flash(f'"{orig.nome}" duplicado com sucesso. Atualize o lote e a quantidade.', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao duplicar medicamento. Tente novamente.', 'danger')
    return redirect(url_for('inventory.listar_medicamentos'))
