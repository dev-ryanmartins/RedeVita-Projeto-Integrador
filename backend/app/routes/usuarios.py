from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.usuario import Usuario
from app.database import db
from app.core.decorators import admin_required, audit_critical_action
from app.utils.log_helper import registrar_log
from app.core.security import criptografar_senha, validar_forca_senha
from app.utils.sanitize import limpar, validar_cpf_digitos

usuarios_bp = Blueprint("usuarios", __name__)


@usuarios_bp.route("/usuarios")
@login_required
@admin_required
def listar_usuarios():
    usuarios = Usuario.query.order_by(Usuario.id).all()
    return render_template("usuarios.html", usuarios=usuarios)


@usuarios_bp.route("/usuarios/cadastrar", methods=["POST"])
@login_required
@admin_required
def cadastrar_usuario_admin():
    """Cadastro direto de usuários pelo painel administrativo."""
    nome = limpar(request.form.get("nome", ""), max_len=150)
    cpf_raw = limpar(request.form.get("cpf", ""), max_len=20)
    cpf = "".join(filter(str.isdigit, cpf_raw))
    email = limpar(request.form.get("email", ""), max_len=150)
    senha = limpar(request.form.get("senha", ""), max_len=128)
    confirmar = limpar(request.form.get("confirmar_senha", ""), max_len=128)
    cargo = limpar(request.form.get("cargo", "Voluntário"), max_len=20)

    if not nome or not cpf or not senha:
        flash("Preencha todos os campos obrigatórios.", "danger")
        return redirect(url_for("usuarios.listar_usuarios"))

    if not validar_cpf_digitos(cpf):
        flash("CPF inválido. Verifique os dígitos e tente novamente.", "danger")
        return redirect(url_for("usuarios.listar_usuarios"))

    # Validação de força de senha
    senha_valida, senha_msg = validar_forca_senha(senha)
    if not senha_valida:
        flash(senha_msg, "danger")
        return redirect(url_for("usuarios.listar_usuarios"))

    if senha != confirmar:
        flash("As senhas não coincidem.", "danger")
        return redirect(url_for("usuarios.listar_usuarios"))

    if Usuario.query.filter_by(cpf=cpf).first():
        flash("Este CPF já está cadastrado no sistema.", "danger")
        return redirect(url_for("usuarios.listar_usuarios"))

    if email and Usuario.query.filter_by(email=email).first():
        flash("Este e-mail já está cadastrado.", "danger")
        return redirect(url_for("usuarios.listar_usuarios"))

    cargos_validos = ["Voluntário", "Farmacêutico", "Médico", "Operador", "Admin", "Doador"]
    cargo = cargo if cargo in cargos_validos else "Voluntário"

    try:
        novo_usuario = Usuario(
            nome=nome,
            cpf=cpf,
            email=email if email else None,
            senha=criptografar_senha(senha),
            cargo=cargo,
            ativo=True,
        )
        db.session.add(novo_usuario)
        db.session.commit()
        registrar_log(
            "Cadastro Admin",
            f'Novo usuário "{nome}" ({cargo}) cadastrado diretamente pelo Admin',
        )
        flash(f"Usuário {nome} cadastrado com sucesso!", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao cadastrar usuário. Tente novamente.", "danger")

    return redirect(url_for("usuarios.listar_usuarios"))


@usuarios_bp.route("/usuario/<int:uid>/cargo", methods=["POST"])
@login_required
@admin_required
def alterar_cargo(uid):
    usuario = db.session.get(Usuario, uid)
    if not usuario:
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("usuarios.listar_usuarios"))

    novo_cargo = request.form.get("cargo", "").strip()
    cargos_validos = ["Voluntário", "Farmacêutico", "Médico", "Operador", "Admin"]
    if novo_cargo not in cargos_validos:
        flash("Cargo inválido.", "danger")
        return redirect(url_for("usuarios.listar_usuarios"))

    cargo_anterior = usuario.cargo
    try:
        usuario.cargo = novo_cargo
        db.session.commit()
        registrar_log(
            "Alteração de Cargo",
            f'Cargo de "{usuario.nome}" alterado de "{cargo_anterior}" para "{novo_cargo}"',
        )
        flash(f"Cargo de {usuario.nome} atualizado para {novo_cargo}.", "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao alterar cargo. Tente novamente.", "danger")

    return redirect(url_for("usuarios.listar_usuarios"))


@usuarios_bp.route("/usuario/<int:uid>/toggle-ativo", methods=["POST"])
@login_required
@admin_required
@audit_critical_action('TOGGLE_USUARIO_ATIVO')
def toggle_ativo(uid):
    from flask_login import current_user

    usuario = db.session.get(Usuario, uid)
    if not usuario:
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("usuarios.listar_usuarios"))

    if usuario.id == current_user.id:
        flash("Você não pode desativar sua própria conta.", "danger")
        return redirect(url_for("usuarios.listar_usuarios"))

    try:
        ativo_atual = usuario.ativo is not False
        usuario.ativo = not ativo_atual
        db.session.commit()
        status = "ativado" if usuario.ativo else "desativado"
        registrar_log("Toggle Usuário", f'Usuário "{usuario.nome}" foi {status}')
        flash(f'Usuário "{usuario.nome}" {status} com sucesso.', "success")
    except Exception:
        db.session.rollback()
        flash("Erro ao alterar status do usuário.", "danger")

    return redirect(url_for("usuarios.listar_usuarios"))
