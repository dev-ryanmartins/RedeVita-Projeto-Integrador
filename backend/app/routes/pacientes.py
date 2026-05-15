import os
import re
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime
from werkzeug.utils import secure_filename
from app.models.paciente import Paciente
from app.models.receita import Receita
from app.models.medico import Medico
from app.models.medicamento import Medicamento
from app.database import db
from app.core.decorators import admin_required, medico_required, farmaceutico_required, cargo_required, equipe_clinica_required
from app.utils.log_helper import registrar_log

pacientes_bp = Blueprint('pacientes', __name__)

TIPOS_RECEITA = [
    'Receita Simples',
    'Receita de Controle Especial (Branca)',
    "Receita 'B' Especial (Azul)",
    "Receita 'A' (Amarela)",
]

_ALLOWED_IMG = {'jpg', 'jpeg', 'png', 'webp', 'pdf'}


def _limpar_cpf(cpf: str) -> str:
    return re.sub(r'\D', '', cpf)


def _allowed_receita_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in _ALLOWED_IMG


def _salvar_imagem_receita(file) -> str | None:
    """Salva o arquivo enviado e retorna o caminho relativo ao static folder."""
    if not file or not file.filename:
        return None
    if not _allowed_receita_file(file.filename):
        return False
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f'rcpt_{uuid.uuid4().hex[:14]}.{ext}'
    upload_dir = os.path.join(current_app.static_folder, 'uploads', 'receitas')
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))
    return f'uploads/receitas/{filename}'


# ─────────────────────────────────────────────────────────────────────────────
# Pacientes
# ─────────────────────────────────────────────────────────────────────────────

@pacientes_bp.route('/pacientes')
@login_required
@equipe_clinica_required
def listar_pacientes():
    pacientes = Paciente.query.order_by(Paciente.nome).all()
    return render_template('pacientes.html', pacientes=pacientes)


@pacientes_bp.route('/paciente/novo', methods=['POST'])
@login_required
@medico_required
def novo_paciente():
    nome = request.form.get('nome', '').strip()
    cpf_raw = request.form.get('cpf', '').strip()
    data_nasc_str = request.form.get('data_nascimento', '').strip()
    endereco = request.form.get('endereco', '').strip()

    cpf = _limpar_cpf(cpf_raw)

    if not nome or not cpf or not data_nasc_str:
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return redirect(url_for('pacientes.listar_pacientes'))

    if len(cpf) != 11:
        flash('CPF inválido. Informe os 11 dígitos.', 'danger')
        return redirect(url_for('pacientes.listar_pacientes'))

    cpf_fmt = f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'

    if Paciente.query.filter_by(cpf=cpf_fmt).first():
        flash(f'CPF "{cpf_fmt}" já está cadastrado.', 'danger')
        return redirect(url_for('pacientes.listar_pacientes'))

    try:
        data_nasc = datetime.strptime(data_nasc_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Data de nascimento inválida.', 'danger')
        return redirect(url_for('pacientes.listar_pacientes'))

    try:
        paciente = Paciente(
            nome=nome,
            cpf=cpf_fmt,
            data_nascimento=data_nasc,
            endereco=endereco or None
        )
        db.session.add(paciente)
        db.session.commit()
        registrar_log('Novo Paciente', f'Paciente "{nome}" ({cpf_fmt}) cadastrado')
        flash(f'Paciente "{nome}" cadastrado com sucesso!', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao cadastrar paciente. Tente novamente.', 'danger')

    return redirect(url_for('pacientes.listar_pacientes'))


@pacientes_bp.route('/paciente/<int:pid>/editar', methods=['POST'])
@login_required
@medico_required
def editar_paciente(pid):
    paciente = db.session.get(Paciente, pid)
    if not paciente:
        flash('Paciente não encontrado.', 'danger')
        return redirect(url_for('pacientes.listar_pacientes'))

    nome = request.form.get('nome', '').strip()
    cpf_raw = request.form.get('cpf', '').strip()
    data_nasc_str = request.form.get('data_nascimento', '').strip()
    endereco = request.form.get('endereco', '').strip()

    cpf = _limpar_cpf(cpf_raw)

    if not nome or not cpf or not data_nasc_str:
        flash('Preencha todos os campos obrigatórios.', 'danger')
        return redirect(url_for('pacientes.listar_pacientes'))

    if len(cpf) != 11:
        flash('CPF inválido.', 'danger')
        return redirect(url_for('pacientes.listar_pacientes'))

    cpf_fmt = f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'
    existente = Paciente.query.filter_by(cpf=cpf_fmt).first()
    if existente and existente.id != pid:
        flash(f'CPF "{cpf_fmt}" já pertence a outro paciente.', 'danger')
        return redirect(url_for('pacientes.listar_pacientes'))

    try:
        data_nasc = datetime.strptime(data_nasc_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Data de nascimento inválida.', 'danger')
        return redirect(url_for('pacientes.listar_pacientes'))

    try:
        paciente.nome = nome
        paciente.cpf = cpf_fmt
        paciente.data_nascimento = data_nasc
        paciente.endereco = endereco or None
        db.session.commit()
        registrar_log('Edição de Paciente', f'Dados do paciente "{nome}" atualizados')
        flash(f'Paciente "{nome}" atualizado com sucesso!', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao atualizar paciente. Tente novamente.', 'danger')

    return redirect(url_for('pacientes.listar_pacientes'))


@pacientes_bp.route('/paciente/<int:pid>/excluir', methods=['POST'])
@login_required
@admin_required
def excluir_paciente(pid):
    paciente = db.session.get(Paciente, pid)
    if not paciente:
        flash('Paciente não encontrado.', 'danger')
        return redirect(url_for('pacientes.listar_pacientes'))

    nome = paciente.nome
    try:
        db.session.delete(paciente)
        db.session.commit()
        registrar_log('Exclusão de Paciente', f'Paciente "{nome}" removido do sistema')
        flash(f'Paciente "{nome}" removido com sucesso.', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao remover paciente. Verifique se há receitas vinculadas.', 'danger')

    return redirect(url_for('pacientes.listar_pacientes'))


# ─────────────────────────────────────────────────────────────────────────────
# Receituário
# ─────────────────────────────────────────────────────────────────────────────

@pacientes_bp.route('/receituario')
@login_required
@cargo_required('Admin', 'Operador', 'Médico', 'Farmacêutico')
def receituario():
    receitas = Receita.query.order_by(Receita.data_emissao.desc()).all()
    pacientes = Paciente.query.order_by(Paciente.nome).all()
    medicos = Medico.query.order_by(Medico.nome).all()
    medicamentos = Medicamento.query.filter(Medicamento.quantidade > 0).order_by(Medicamento.nome).all()
    return render_template(
        'receituario.html',
        receitas=receitas,
        pacientes=pacientes,
        medicos=medicos,
        medicamentos=medicamentos,
        tipos_receita=TIPOS_RECEITA,
    )


@pacientes_bp.route('/receita/nova', methods=['POST'])
@login_required
@medico_required
def nova_receita():
    paciente_id = request.form.get('paciente_id', type=int)
    medico_id = request.form.get('medico_id', type=int)
    medicamento_id = request.form.get('medicamento_id', type=int) or None
    observacoes = request.form.get('observacoes', '').strip()
    tipo_receita = request.form.get('tipo_receita', '').strip() or None

    if not paciente_id or not medico_id:
        flash('Selecione o paciente e o médico.', 'danger')
        return redirect(url_for('pacientes.receituario'))

    paciente = db.session.get(Paciente, paciente_id)
    medico = db.session.get(Medico, medico_id)
    if not paciente or not medico:
        flash('Paciente ou médico não encontrado.', 'danger')
        return redirect(url_for('pacientes.receituario'))

    if medicamento_id:
        med = db.session.get(Medicamento, medicamento_id)
        if med and med.controlado and not tipo_receita:
            flash(
                f'"{med.nome}" é um medicamento controlado (Portaria 344). '
                'O tipo de receita especial é obrigatório.',
                'danger'
            )
            return redirect(url_for('pacientes.receituario'))

    # ── Upload de imagem da receita ──────────────────────────────────────────
    file = request.files.get('imagem_receita')
    imagem_url = None
    if file and file.filename:
        resultado = _salvar_imagem_receita(file)
        if resultado is False:
            flash('Formato de imagem não suportado. Use JPG, PNG, WEBP ou PDF.', 'danger')
            return redirect(url_for('pacientes.receituario'))
        imagem_url = resultado

    try:
        receita = Receita(
            paciente_id=paciente_id,
            medico_id=medico_id,
            medicamento_id=medicamento_id,
            observacoes=observacoes or None,
            tipo_receita=tipo_receita,
            imagem_url=imagem_url,
            status='pendente'
        )
        db.session.add(receita)
        db.session.commit()

        med_nome = ''
        if medicamento_id:
            m = db.session.get(Medicamento, medicamento_id)
            med_nome = f' — {m.nome}' if m else ''
            if m and m.controlado:
                registrar_log(
                    'Portaria 344 - Nova Receita',
                    f'Receita CONTROLADA emitida por Dr(a). "{medico.nome}" (CRM: {medico.crm}) '
                    f'para "{paciente.nome}"{med_nome} | Tipo: {tipo_receita}'
                    + (' | Com imagem digitalizada' if imagem_url else '')
                )
            else:
                registrar_log(
                    'Nova Receita',
                    f'Receita emitida por Dr(a). "{medico.nome}" para "{paciente.nome}"{med_nome}'
                    + (' | Com imagem digitalizada' if imagem_url else '')
                )
        else:
            registrar_log(
                'Nova Receita',
                f'Receita emitida por Dr(a). "{medico.nome}" para "{paciente.nome}"'
                + (' | Com imagem digitalizada' if imagem_url else '')
            )

        flash('Ordem de retirada emitida com sucesso!', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao emitir receita. Tente novamente.', 'danger')

    return redirect(url_for('pacientes.receituario'))


@pacientes_bp.route('/receita/<int:rid>/dar-baixa', methods=['POST'])
@login_required
@farmaceutico_required
def dar_baixa_receita(rid):
    receita = db.session.get(Receita, rid)
    if not receita:
        flash('Receita não encontrada.', 'danger')
        return redirect(url_for('pacientes.receituario'))

    if receita.status == 'dispensada':
        flash('Esta receita já foi dispensada anteriormente.', 'warning')
        return redirect(url_for('pacientes.receituario'))

    if receita.medicamento and receita.medicamento.controlado:
        if not receita.tipo_receita:
            flash(
                f'Não é possível dispensar "{receita.medicamento.nome}" (Portaria 344) sem '
                'o tipo de receita especial. Edite a ordem e informe o tipo antes de dispensar.',
                'danger'
            )
            return redirect(url_for('pacientes.receituario'))

        crm = receita.medico.crm if receita.medico else ''
        if not crm or len(re.sub(r'\D', '', crm)) < 4:
            flash(
                'CRM do médico prescriptor inválido ou não cadastrado. '
                'Verifique o cadastro do médico antes de dispensar.',
                'danger'
            )
            return redirect(url_for('pacientes.receituario'))

    try:
        receita.status = 'dispensada'
        receita.dispensada_em = datetime.utcnow()
        receita.dispensada_por_id = current_user.id
        db.session.commit()

        if receita.medicamento and receita.medicamento.controlado:
            registrar_log(
                'Portaria 344 - Dispensação',
                f'Receita CONTROLADA #{receita.id} — "{receita.medicamento.nome}" — '
                f'Paciente "{receita.paciente.nome}" — CRM {receita.medico.crm} — '
                f'Receita: {receita.tipo_receita} — dispensada por {current_user.nome}'
            )
        else:
            registrar_log(
                'Dispensação de Receita',
                f'Receita #{receita.id} — Paciente "{receita.paciente.nome}" — '
                f'dispensada por {current_user.nome}'
            )

        flash(f'Receita #{receita.id} dispensada com sucesso!', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro ao dar baixa na receita. Tente novamente.', 'danger')

    return redirect(url_for('pacientes.receituario'))
