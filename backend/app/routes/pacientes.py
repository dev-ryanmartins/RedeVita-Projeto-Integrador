import os
import re
import uuid
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.models.paciente import Paciente
from app.models.receita import Receita
from app.models.medico import Medico
from app.models.medicamento import Medicamento
from app.database import db
from app.core.decorators import (
    admin_required,
    medico_required,
    farmaceutico_required,
    cargo_required,
    equipe_clinica_required,
)
from app.utils.log_helper import registrar_log
from app.utils.storage import get_storage_service
from app.utils.notificacoes import enviar_notificacao_dispensacao
from app.utils.email_service import email_service
from app.utils.sms_service import sms_service

pacientes_bp = Blueprint("pacientes", __name__)

TIPOS_RECEITA = [
    "Receita Simples",
    "Receita de Controle Especial (Branca)",
    "Receita 'B' Especial (Azul)",
    "Receita 'A' (Amarela)",
]

_ALLOWED_IMG = {"jpg", "jpeg", "png", "webp", "pdf"}


def _limpar_cpf(cpf: str) -> str:
    return re.sub(r"\D", "", cpf)


def _allowed_receita_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in _ALLOWED_IMG


def _validate_file_magic_bytes(file) -> tuple[bool, str]:
    """
    Valida o tipo real do arquivo usando magic bytes.
    Retorna (is_valid, error_message).
    """
    # Magic bytes signatures
    MAGIC_BYTES = {
        b'\xFF\xD8\xFF': 'jpg',
        b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A': 'png',
        b'\x52\x49\x46\x46': 'webp',  # RIFF header (WEBP uses this)
        b'%PDF': 'pdf',
    }
    
    # Read first 8 bytes for magic byte detection
    file.seek(0)
    header = file.read(8)
    file.seek(0)  # Reset file pointer
    
    if not header:
        return False, "Arquivo vazio ou corrompido"
    
    # Check magic bytes
    for magic, file_type in MAGIC_BYTES.items():
        if header.startswith(magic):
            return True, file_type
    
    return False, "Tipo de arquivo não detectado. Arquivo pode estar corrompido ou disfarçado."


def _salvar_imagem_receita(file) -> str | None:
    """Salva o arquivo enviado em storage configurável e retorna o caminho/URL."""
    if not file or not file.filename:
        return None
    if not _allowed_receita_file(file.filename):
        return False

    # Validate magic bytes
    is_valid, detected_type = _validate_file_magic_bytes(file)
    if not is_valid:
        return False

    ext = detected_type if detected_type in _ALLOWED_IMG else file.filename.rsplit(".", 1)[1].lower()
    filename = f"receita_{uuid.uuid4().hex[:14]}.{ext}"

    storage = get_storage_service()
    storage_path = storage.save_file(file, filename, folder="receitas")
    return storage_path

# ─────────────────────────────────────────────────────────────────────────────
# Pacientes
# ─────────────────────────────────────────────────────────────────────────────


@pacientes_bp.route("/pacientes")
@login_required
@equipe_clinica_required
def listar_pacientes():
    pacientes = Paciente.query.order_by(Paciente.nome).all()
    return render_template("pacientes.html", pacientes=pacientes)


@pacientes_bp.route("/paciente/novo", methods=["POST"])
@login_required
@medico_required
def novo_paciente():
    nome = request.form.get("nome", "").strip()
    cpf_raw = request.form.get("cpf", "").strip()
    data_nasc_str = request.form.get("data_nascimento", "").strip()
    endereco = request.form.get("endereco", "").strip()

    cpf = _limpar_cpf(cpf_raw)

    if not nome or not cpf or not data_nasc_str:
        flash("Preencha todos os campos obrigatórios.", "danger")
        return redirect(url_for("pacientes.listar_pacientes"))

    if len(cpf) != 11:
        flash("CPF inválido. Informe os 11 dígitos.", "danger")
        return redirect(url_for("pacientes.listar_pacientes"))

    cpf_fmt = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

    if Paciente.query.filter_by(cpf=cpf_fmt).first():
        flash(f'CPF "{cpf_fmt}" já está cadastrado.', "danger")
        return redirect(url_for("pacientes.listar_pacientes"))

    try:
        data_nasc = datetime.strptime(data_nasc_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Data de nascimento inválida.", "danger")
        return redirect(url_for("pacientes.listar_pacientes"))

    try:
        paciente = Paciente(
            nome=nome, cpf=cpf_fmt, data_nascimento=data_nasc, endereco=endereco or None
        )
        db.session.add(paciente)
        db.session.commit()
        registrar_log("Novo Paciente", f'Paciente "{nome}" ({cpf_fmt}) cadastrado')
        flash(f'Paciente "{nome}" cadastrado com sucesso!', "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao cadastrar paciente. Tente novamente.", "danger")

    return redirect(url_for("pacientes.listar_pacientes"))


@pacientes_bp.route("/paciente/<int:pid>/editar", methods=["POST"])
@login_required
@medico_required
def editar_paciente(pid):
    paciente = db.session.get(Paciente, pid)
    if not paciente:
        flash("Paciente não encontrado.", "danger")
        return redirect(url_for("pacientes.listar_pacientes"))

    nome = request.form.get("nome", "").strip()
    cpf_raw = request.form.get("cpf", "").strip()
    data_nasc_str = request.form.get("data_nascimento", "").strip()
    endereco = request.form.get("endereco", "").strip()

    cpf = _limpar_cpf(cpf_raw)

    if not nome or not cpf or not data_nasc_str:
        flash("Preencha todos os campos obrigatórios.", "danger")
        return redirect(url_for("pacientes.listar_pacientes"))

    if len(cpf) != 11:
        flash("CPF inválido.", "danger")
        return redirect(url_for("pacientes.listar_pacientes"))

    cpf_fmt = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    existente = Paciente.query.filter_by(cpf=cpf_fmt).first()
    if existente and existente.id != pid:
        flash(f'CPF "{cpf_fmt}" já pertence a outro paciente.', "danger")
        return redirect(url_for("pacientes.listar_pacientes"))

    try:
        data_nasc = datetime.strptime(data_nasc_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Data de nascimento inválida.", "danger")
        return redirect(url_for("pacientes.listar_pacientes"))

    try:
        paciente.nome = nome
        paciente.cpf = cpf_fmt
        paciente.data_nascimento = data_nasc
        paciente.endereco = endereco or None
        db.session.commit()
        registrar_log("Edição de Paciente", f'Dados do paciente "{nome}" atualizados')
        flash(f'Paciente "{nome}" atualizado com sucesso!', "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao atualizar paciente. Tente novamente.", "danger")

    return redirect(url_for("pacientes.listar_pacientes"))


@pacientes_bp.route("/paciente/<int:pid>/excluir", methods=["POST"])
@login_required
@admin_required
def excluir_paciente(pid):
    paciente = db.session.get(Paciente, pid)
    if not paciente:
        flash("Paciente não encontrado.", "danger")
        return redirect(url_for("pacientes.listar_pacientes"))

    nome = paciente.nome
    try:
        db.session.delete(paciente)
        db.session.commit()
        registrar_log("Exclusão de Paciente", f'Paciente "{nome}" removido do sistema')
        flash(f'Paciente "{nome}" removido com sucesso.', "success")
    except Exception:
        db.session.rollback()
        flash(
            "Erro ao remover paciente. Verifique se há receitas vinculadas.", "danger"
        )

    return redirect(url_for("pacientes.listar_pacientes"))


# ─────────────────────────────────────────────────────────────────────────────
# Receituário
# ─────────────────────────────────────────────────────────────────────────────


@pacientes_bp.route("/receituario")
@login_required
@cargo_required("Admin", "Operador", "Médico", "Farmacêutico")
def receituario():
    pagina = request.args.get("page", 1, type=int)
    por_pagina = 20
    
    try:
        receitas = Receita.query.order_by(Receita.data_emissao.desc()).paginate(
            page=pagina, per_page=por_pagina, error_out=False
        )
    except Exception:
        receitas = None
    
    try:
        pacientes = Paciente.query.order_by(Paciente.nome).all()
    except Exception:
        pacientes = []
    
    try:
        medicos = Medico.query.order_by(Medico.nome).all()
    except Exception:
        medicos = []
    
    try:
        medicamentos = (
            Medicamento.query.filter(Medicamento.quantidade > 0)
            .order_by(Medicamento.nome)
            .all()
        )
    except Exception:
        medicamentos = []
    
    try:
        total_pendentes = Receita.query.filter_by(status="pendente").count()
    except Exception:
        total_pendentes = 0
    
    try:
        total_dispensadas = Receita.query.filter_by(status="dispensada").count()
    except Exception:
        total_dispensadas = 0
    
    try:
        total_controladas = (
            Receita.query.join(Medicamento)
            .filter(Medicamento.tarja == "Portaria 344")
            .count()
        )
    except Exception:
        total_controladas = 0
    
    return render_template(
        "receituario.html",
        receitas=receitas,
        pacientes=pacientes,
        medicos=medicos,
        medicamentos=medicamentos,
        tipos_receita=TIPOS_RECEITA,
        total_pendentes=total_pendentes,
        total_dispensadas=total_dispensadas,
        total_controladas=total_controladas,
    )


@pacientes_bp.route("/receita/nova", methods=["POST"])
@login_required
@medico_required
def nova_receita():
    paciente_id = request.form.get("paciente_id", type=int)
    medico_id = request.form.get("medico_id", type=int)
    medicamento_id = request.form.get("medicamento_id", type=int) or None
    observacoes = request.form.get("observacoes", "").strip()
    tipo_receita = request.form.get("tipo_receita", "").strip() or None

    if not paciente_id or not medico_id:
        flash("Selecione o paciente e o médico.", "danger")
        return redirect(url_for("pacientes.receituario"))

    paciente = db.session.get(Paciente, paciente_id)
    medico = db.session.get(Medico, medico_id)
    if not paciente or not medico:
        flash("Paciente ou médico não encontrado.", "danger")
        return redirect(url_for("pacientes.receituario"))

    if medicamento_id:
        med = db.session.get(Medicamento, medicamento_id)
        if med and med.controlado and not tipo_receita:
            flash(
                f'"{med.nome}" é um medicamento controlado (Portaria 344). '
                "O tipo de receita especial é obrigatório.",
                "danger",
            )
            return redirect(url_for("pacientes.receituario"))

    # ── Upload de imagem da receita ──────────────────────────────────────────
    file = request.files.get("imagem_receita")
    imagem_url = None
    if file and file.filename:
        resultado = _salvar_imagem_receita(file)
        if resultado is False:
            flash(
                "Formato de imagem não suportado. Use JPG, PNG, WEBP ou PDF.", "danger"
            )
            return redirect(url_for("pacientes.receituario"))
        imagem_url = resultado

    try:
        receita = Receita(
            paciente_id=paciente_id,
            medico_id=medico_id,
            medicamento_id=medicamento_id,
            observacoes=observacoes or None,
            tipo_receita=tipo_receita,
            imagem_url=imagem_url,
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
                    "Portaria 344 - Nova Receita",
                    f'Receita CONTROLADA emitida por Dr(a). "{medico.nome}" (CRM: {medico.crm}) '
                    f'para "{paciente.nome}"{med_nome} | Tipo: {tipo_receita}'
                    + (" | Com imagem digitalizada" if imagem_url else ""),
                )
            else:
                registrar_log(
                    "Nova Receita",
                    f'Receita emitida por Dr(a). "{medico.nome}" para "{paciente.nome}"{med_nome}'
                    + (" | Com imagem digitalizada" if imagem_url else ""),
                )
        else:
            registrar_log(
                "Nova Receita",
                f'Receita emitida por Dr(a). "{medico.nome}" para "{paciente.nome}"'
                + (" | Com imagem digitalizada" if imagem_url else ""),
            )

        flash("Ordem de retirada emitida com sucesso!", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao emitir receita. Tente novamente.", "danger")

    return redirect(url_for("pacientes.receituario"))


@pacientes_bp.route("/receita/<int:rid>/dar-baixa", methods=["POST"])
@login_required
@farmaceutico_required
def dar_baixa_receita(rid):
    receita = db.session.get(Receita, rid)
    if not receita:
        flash("Receita não encontrada.", "danger")
        return redirect(url_for("pacientes.receituario"))

    if receita.status == "dispensada":
        flash("Esta receita já foi dispensada anteriormente.", "warning")
        return redirect(url_for("pacientes.receituario"))

    if receita.medicamento and receita.medicamento.controlado:
        if not receita.tipo_receita:
            flash(
                f'Não é possível dispensar "{receita.medicamento.nome}" (Portaria 344) sem '
                "o tipo de receita especial. Edite a ordem e informe o tipo antes de dispensar.",
                "danger",
            )
            return redirect(url_for("pacientes.receituario"))

        crm = receita.medico.crm if receita.medico else ""
        if not crm or len(re.sub(r"\D", "", crm)) < 4:
            flash(
                "CRM do médico prescriptor inválido ou não cadastrado. "
                "Verifique o cadastro do médico antes de dispensar.",
                "danger",
            )
            return redirect(url_for("pacientes.receituario"))

    try:
        receita.status = "dispensada"
        receita.dispensada_em = datetime.utcnow()
        receita.dispensada_por_id = current_user.id
        db.session.commit()

        if receita.medicamento and receita.medicamento.controlado:
            registrar_log(
                "Portaria 344 - Dispensação",
                f'Receita CONTROLADA #{receita.id} — "{receita.medicamento.nome}" — '
                f'Paciente "{receita.paciente.nome}" — CRM {receita.medico.crm} — '
                f"Receita: {receita.tipo_receita} — dispensada por {current_user.nome}",
            )
        else:
            registrar_log(
                "Dispensação de Receita",
                f'Receita #{receita.id} — Paciente "{receita.paciente.nome}" — '
                f"dispensada por {current_user.nome}",
            )
        
        # Enviar notificações de dispensação
        codigo_reserva = f"RES-{receita.id:06d}"
        medicamento_nome = receita.medicamento.nome if receita.medicamento else "Medicamento"
        endereco_coleta = "Farmácia Central - Av. Principal, 1000"  # Em produção, buscar da farmácia real
        data_limite = (receita.dispensada_em + timedelta(days=7)).strftime('%d/%m/%Y')
        
        # Enviar e-mail se paciente tiver e-mail cadastrado
        if receita.paciente and hasattr(receita.paciente, 'email') and receita.paciente.email:
            email_service.send_reserva_confirmation_async(
                to_email=receita.paciente.email,
                nome_paciente=receita.paciente.nome,
                medicamento=medicamento_nome,
                codigo_reserva=codigo_reserva,
                endereco_coleta=endereco_coleta,
                data_limite=data_limite
            )
        
        # Enviar SMS se paciente tiver telefone cadastrado
        if receita.paciente and hasattr(receita.paciente, 'telefone') and receita.paciente.telefone:
            sms_service.send_reserva_confirmation_async(
                to_phone=receita.paciente.telefone,
                codigo_reserva=codigo_reserva,
                endereco=endereco_coleta
            )
        
        # Enviar notificação WhatsApp existente (compatibilidade)
        if receita.paciente and hasattr(receita.paciente, 'telefone') and receita.paciente.telefone:
            telefone = receita.paciente.telefone
            if not telefone.startswith('+'):
                telefone = '+55' + ''.join(c for c in telefone if c.isdigit())
            
            notif_result = enviar_notificacao_dispensacao(
                telefone=telefone,
                paciente_nome=receita.paciente.nome,
                medicamento_nome=medicamento_nome
            )
            if notif_result.get('enviado'):
                print(f"Notificação não enviada: {notif_result.get('mensagem')}")

        flash(f"Receita #{receita.id} dispensada com sucesso!", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao dar baixa na receita. Tente novamente.", "danger")

    return redirect(url_for("pacientes.receituario"))
