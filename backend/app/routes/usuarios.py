from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.usuario import Usuario
from app.database import db
from app.core.decorators import admin_required
from app.utils.log_helper import registrar_log

usuarios_bp = Blueprint("usuarios", __name__)


@usuarios_bp.route("/usuarios")
@login_required
@admin_required
def listar_usuarios():
    usuarios = Usuario.query.order_by(Usuario.id).all()
    return render_template("usuarios.html", usuarios=usuarios)


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
