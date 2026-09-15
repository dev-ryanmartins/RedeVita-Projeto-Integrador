from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    session,
)
import secrets
import time
import re
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from app.models.usuario import Usuario
from app.core.security import verificar_senha, criptografar_senha, validar_forca_senha
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
        identificador_raw = limpar(request.form.get("identificador", ""), max_len=150)
        cpf = "".join(filter(str.isdigit, identificador_raw))
        senha = limpar(request.form.get("senha", ""), max_len=128)

        usuario = None
        if "@" in identificador_raw:
            usuario = Usuario.query.filter(Usuario.email.ilike(identificador_raw.strip())).first()
        if not usuario and len(cpf) == 11:
            usuario = Usuario.query.filter_by(cpf=cpf).first()
        if not usuario and identificador_raw:
            usuario = Usuario.query.filter(
                db.or_(
                    Usuario.email.ilike(identificador_raw.strip()),
                    Usuario.cpf == identificador_raw.strip(),
                    Usuario.cpf == cpf
                )
            ).first()

        if usuario and verificar_senha(usuario.senha, senha):
            if usuario.ativo is False:
                flash("Sua conta está desativada. Contate o administrador.", "danger")
                registrar_log(
                    "Login Bloqueado",
                    f"Tentativa de login de conta desativada (Identificador: {identificador_raw[:3]}***) — IP: {request.remote_addr}",
                )
                return render_template("login.html")
            login_user(usuario)
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            session['usuario_cargo'] = usuario.cargo
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
            f'Tentativa de login inválida (Identificador: {identificador_raw[:3] if identificador_raw else "?"}***) — IP: {request.remote_addr}',
        )
        flash("CPF, e-mail ou senha incorretos.", "danger")
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

        # Validação de força de senha
        senha_valida, senha_msg = validar_forca_senha(senha)
        if not senha_valida:
            flash(senha_msg, "danger")
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
    "5 per minute; 20 per hour",
    methods=["POST"],
    error_message="Muitas solicitações. Aguarde antes de tentar novamente.",
)
def recuperar_senha():
    if request.method == "POST":
        identificador = limpar(request.form.get("identificador", "") or request.form.get("email", ""), max_len=150)
        clean_cpf = "".join(filter(str.isdigit, identificador))

        usuario = None
        if "@" in identificador:
            usuario = Usuario.query.filter(Usuario.email.ilike(identificador.strip())).first()
        elif len(clean_cpf) == 11:
            usuario = Usuario.query.filter_by(cpf=clean_cpf).first()

        if not usuario and identificador:
            usuario = Usuario.query.filter(
                db.or_(
                    Usuario.email.ilike(identificador.strip()),
                    Usuario.cpf == identificador.strip(),
                    Usuario.cpf == clean_cpf
                )
            ).first()

        if not usuario:
            flash("Nenhum usuário localizado com o e-mail ou CPF informado.", "danger")
            return render_template("recuperar_senha.html")

        # Gera código de 6 dígitos numérico seguro
        codigo = str(secrets.randbelow(900000) + 100000)
        user_email = usuario.email or f"{usuario.cpf}@redevita.local"

        session["pwd_recovery"] = {
            "user_id": usuario.id,
            "email": user_email,
            "nome": usuario.nome,
            "codigo": codigo,
            "expira_em": time.time() + 900,
            "verificado": False,
        }

        # Log seguro e auditoria
        current_app.logger.info(f"[RedeVita Segurança] Código de recuperação gerado para {user_email}: {codigo}")
        registrar_log(
            "Recuperação de Senha",
            f'Código de verificação de 6 dígitos gerado para "{usuario.nome}" ({user_email}) — IP: {request.remote_addr}',
        )

        return redirect(url_for("auth.verificar_codigo"))

    return render_template("recuperar_senha.html")


@auth_bp.route("/verificar-codigo", methods=["GET", "POST"])
def verificar_codigo():
    rec = session.get("pwd_recovery")
    if not rec:
        return redirect(url_for("auth.recuperar_senha"))

    user_email = rec.get("email", "")
    parts = user_email.split("@")
    u_part = parts[0]
    domain = parts[1] if len(parts) > 1 else "redevita.local"
    masked_user = u_part[0] + "*" * max(2, len(u_part) - 2) + u_part[-1] if len(u_part) > 2 else u_part + "***"
    masked_email = f"{masked_user}@{domain}"

    if request.method == "POST":
        if time.time() > rec.get("expira_em", 0):
            flash("O código de verificação expirou após 15 minutos. Solicite um novo código.", "danger")
            return render_template("verificar_codigo.html", masked_email=masked_email, preview_code=None)

        codigo_digitado = re.sub(r"\D", "", request.form.get("codigo", ""))
        if codigo_digitado != rec.get("codigo"):
            flash("Código de verificação incorreto. Digite exatamente os 6 dígitos recebidos.", "danger")
            return render_template("verificar_codigo.html", masked_email=masked_email, preview_code=rec.get("codigo"))

        rec["verificado"] = True
        session["pwd_recovery"] = rec
        registrar_log(
            "Recuperação de Senha",
            f'Código de 6 dígitos validado com sucesso para "{rec.get("nome")}" — IP: {request.remote_addr}',
        )
        return redirect(url_for("auth.redefinir_senha"))

    return render_template("verificar_codigo.html", masked_email=masked_email, preview_code=rec.get("codigo"))


@auth_bp.route("/redefinir-senha", methods=["GET", "POST"])
def redefinir_senha():
    rec = session.get("pwd_recovery")
    if not rec or not rec.get("verificado"):
        flash("Sessão de verificação expirada ou inválida. Inicie a recuperação novamente.", "danger")
        return redirect(url_for("auth.recuperar_senha"))

    if request.method == "POST":
        nova_senha = limpar(request.form.get("nova_senha", ""), max_len=128)
        confirmar = limpar(request.form.get("confirmar_senha", ""), max_len=128)

        senha_valida, senha_msg = validar_forca_senha(nova_senha)
        if not senha_valida:
            flash(senha_msg, "danger")
            return render_template("redefinir_senha.html")

        if nova_senha != confirmar:
            flash("As senhas não coincidem.", "danger")
            return render_template("redefinir_senha.html")

        usuario = Usuario.query.get(rec.get("user_id"))
        if usuario:
            try:
                usuario.senha = criptografar_senha(nova_senha)
                db.session.commit()
                registrar_log(
                    "Redefinição de Senha",
                    f'Senha do usuário "{usuario.nome}" redefinida com sucesso — IP: {request.remote_addr}',
                )
                session.pop("pwd_recovery", None)
                flash("Senha atualizada com sucesso! Acesse sua conta com as novas credenciais.", "success")
                return redirect(url_for("auth.login"))
            except Exception:
                db.session.rollback()
                flash("Erro ao atualizar senha no banco de dados. Tente novamente.", "danger")
        else:
            flash("Usuário não encontrado.", "danger")
            return redirect(url_for("auth.login"))

    return render_template("redefinir_senha.html")


@auth_bp.route("/redefinir-senha/<token>", methods=["GET", "POST"])
def redefinir_senha_token(token):
    s = _get_serializer()
    try:
        email = s.loads(token, salt="password-reset-salt", max_age=900)
    except (SignatureExpired, BadSignature):
        flash("O link expirou ou é inválido. Solicite um novo.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        nova_senha = limpar(request.form.get("nova_senha", ""), max_len=128)
        confirmar = limpar(request.form.get("confirmar_senha", ""), max_len=128)

        senha_valida, senha_msg = validar_forca_senha(nova_senha)
        if not senha_valida:
            flash(senha_msg, "danger")
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
def logout():
    try:
        if current_user and current_user.is_authenticated:
            registrar_log(
                "Logout",
                f'Usuário "{current_user.nome}" saiu do sistema — IP: {request.remote_addr}',
            )
            logout_user()
    except Exception:
        pass
    from flask import session as flask_session
    flask_session.clear()
    resposta = redirect(url_for("auth.login"))
    cookie_name = current_app.config.get("SESSION_COOKIE_NAME", "session")
    remember_cookie = current_app.config.get("REMEMBER_COOKIE_NAME", "remember_token")
    resposta.delete_cookie(cookie_name, path="/")
    resposta.delete_cookie(remember_cookie, path="/")
    resposta.delete_cookie("redevita_token", path="/")
    resposta.delete_cookie("connect.sid", path="/")
    flash("Você saiu do sistema com sucesso.", "info")
    return resposta
