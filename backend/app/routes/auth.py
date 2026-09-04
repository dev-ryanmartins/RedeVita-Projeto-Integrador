from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from app.models.usuario import Usuario
from app.core.security import verificar_senha, criptografar_senha
from app.core.jwt_auth import gerar_token
from app.utils.log_helper import registrar_log
from app.utils.sanitize import limpar, validar_cpf_digitos
from app.extensions import limiter
from app.database import db

auth_bp = Blueprint("auth", __name__)


def _get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit(
    "5 per minute; 30 per hour",
    methods=["POST"],
    error_message="Muitas tentativas de login. Aguarde alguns minutos.",
)
def login():
    if current_user.is_authenticated:
        return redirect(url_for("inventory.dashboard"))

    if request.method == "POST":
        cpf_raw = limpar(request.form.get("identificador", ""), max_len=20)
        cpf = "".join(filter(str.isdigit, cpf_raw))
        senha = limpar(request.form.get("senha", ""), max_len=128)

        usuario = Usuario.query.filter_by(cpf=cpf).first()

        if usuario and verificar_senha(usuario.senha, senha):
            if usuario.ativo is False:
                flash("Sua conta está desativada. Contate o administrador.", "danger")
                registrar_log(
                    "Login Bloqueado",
                    f"Tentativa de login de conta desativada (CPF: {cpf[:3]}***) — IP: {request.remote_addr}",
                )
                return render_template("login.html")
            login_user(usuario)
            registrar_log(
                "Login",
                f'Usuário "{usuario.nome}" ({usuario.cargo}) fez login — IP: {request.remote_addr}',
            )
            token = gerar_token(usuario)
            
            # Redirecionamento padrão para dashboard
            redirect_url = url_for("inventory.dashboard")
            
            resposta = redirect(redirect_url)
            resposta.set_cookie(
                "redevita_token", token, httponly=True, samesite="Lax", max_age=3600
            )
            return resposta

        registrar_log(
            "Login Falhou",
            f'Tentativa de login inválida (CPF: {cpf[:3] if cpf else "?"}***) — IP: {request.remote_addr}',
        )
        flash("CPF ou senha incorretos.", "danger")
    return render_template("login.html")


@auth_bp.route("/cadastro", methods=["GET", "POST"])
@limiter.limit(
    "5 per minute",
    methods=["POST"],
    error_message="Muitas tentativas de cadastro. Aguarde um momento.",
)
def cadastro():
    if request.method == "POST":
        nome = limpar(request.form.get("nome", ""), max_len=150)
        cpf_raw = limpar(request.form.get("cpf", ""), max_len=20)
        cpf = "".join(filter(str.isdigit, cpf_raw))
        email = limpar(request.form.get("email", ""), max_len=150)
        senha = limpar(request.form.get("senha", ""), max_len=128)
        confirmar = limpar(request.form.get("confirmar_senha", ""), max_len=128)

        if not nome or not cpf or not senha:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template("cadastro.html")

        if not validar_cpf_digitos(cpf):
            flash("CPF inválido. Verifique os dígitos e tente novamente.", "danger")
            return render_template("cadastro.html")

        if len(senha) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "danger")
            return render_template("cadastro.html")

        if senha != confirmar:
            flash("As senhas não coincidem.", "danger")
            return render_template("cadastro.html")

        if Usuario.query.filter_by(cpf=cpf).first():
            flash("Este CPF já está cadastrado no sistema.", "danger")
            return render_template("cadastro.html")

        if email and Usuario.query.filter_by(email=email).first():
            flash("Este e-mail já está cadastrado.", "danger")
            return render_template("cadastro.html")

        cargo_raw = limpar(request.form.get("cargo", "Voluntário"), max_len=20)
        cargos_validos = ["Voluntário", "Farmacêutico", "Médico", "Operador", "Admin", "Doador"]
        cargo = cargo_raw if cargo_raw in cargos_validos else "Voluntário"

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
                "Cadastro",
                f'Novo usuário "{nome}" ({cargo}) cadastrado — IP: {request.remote_addr}',
            )
            flash("Cadastro realizado com sucesso! Faça o login.", "success")
            return redirect(url_for("auth.login"))
        except Exception:
            db.session.rollback()
            flash("Erro ao realizar cadastro. Tente novamente.", "danger")

    return render_template("cadastro.html")


@auth_bp.route("/recuperar-senha", methods=["GET", "POST"])
@limiter.limit(
    "3 per minute; 10 per hour",
    methods=["POST"],
    error_message="Muitas solicitações. Aguarde antes de tentar novamente.",
)
def recuperar_senha():
    if request.method == "POST":
        email = limpar(request.form.get("email", ""), max_len=150)
        usuario = Usuario.query.filter_by(email=email).first()

        if usuario:
            s = _get_serializer()
            token = s.dumps(email, salt="password-reset-salt")
            link = url_for("auth.redefinir_senha", token=token, _external=True)
            current_app.logger.info(f"Link de redefinição para {email}: {link}")

        flash(
            "Se o e-mail existir no sistema, você receberá o link de recuperação em breve.",
            "info",
        )
        return redirect(url_for("auth.login"))
    return render_template("recuperar_senha.html")


@auth_bp.route("/redefinir-senha/<token>", methods=["GET", "POST"])
def redefinir_senha(token):
    s = _get_serializer()
    try:
        # Reduced from 1800 (30 min) to 900 (15 min) for stricter security
        email = s.loads(token, salt="password-reset-salt", max_age=900)
    except (SignatureExpired, BadSignature):
        flash("O link expirou ou é inválido. Solicite um novo.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        nova_senha = limpar(request.form.get("nova_senha", ""), max_len=128)
        confirmar = limpar(request.form.get("confirmar_senha", ""), max_len=128)

        if len(nova_senha) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "danger")
            return render_template("redefinir_senha.html")

        if nova_senha != confirmar:
            flash("As senhas não coincidem.", "danger")
            return render_template("redefinir_senha.html")

        usuario = Usuario.query.filter_by(email=email).first()
        if usuario:
            try:
                usuario.senha = criptografar_senha(nova_senha)
                db.session.commit()
                registrar_log(
                    "Redefinição de Senha",
                    f'Senha do usuário "{usuario.nome}" redefinida — IP: {request.remote_addr}',
                )
                flash("Senha atualizada com sucesso!", "success")
            except Exception:
                db.session.rollback()
                flash("Erro ao atualizar senha. Tente novamente.", "danger")
        else:
            flash("Usuário não encontrado.", "danger")
        return redirect(url_for("auth.login"))

    return render_template("redefinir_senha.html")


@auth_bp.route("/logout")
@login_required
def logout():
    registrar_log(
        "Logout",
        f'Usuário "{current_user.nome}" saiu do sistema — IP: {request.remote_addr}',
    )
    logout_user()
    resposta = redirect(url_for("auth.login"))
    resposta.delete_cookie("redevita_token")
    flash("Você saiu do sistema.", "info")
    return resposta
