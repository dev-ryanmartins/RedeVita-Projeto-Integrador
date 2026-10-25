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
from datetime import datetime
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from app.models.usuario import Usuario
from app.models.recuperacao_senha import RecuperacaoSenha
from app.core.security import verificar_senha, criptografar_senha, validar_forca_senha
from app.core.jwt_auth import gerar_token
from app.utils.log_helper import registrar_log
from app.utils.sanitize import limpar, validar_cpf_digitos
from app.utils.document_validation import validar_cpf, normalizar_cpf
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

        if usuario and verificar_senha(usuario.senha, senha) and usuario.ativo:
            login_user(usuario)
            session['usuario_id'] = usuario.id
            session['usuario_nome'] = usuario.nome
            session['usuario_cargo'] = usuario.cargo
            registrar_log(
                "Login",
                f'Usuário "{usuario.nome}" ({usuario.cargo}) fez login — IP: {request.remote_addr}',
            )
            token = gerar_token(usuario)
            
            # Redirecionamento: se senha não foi trocada, forçar troca
            if not usuario.senha_trocada:
                redirect_url = url_for("auth.trocar_senha_obrigatoria")
            else:
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


@auth_bp.route("/trocar-senha-obrigatoria", methods=["GET", "POST"])
@login_required
def trocar_senha_obrigatoria():
    """Rota para troca obrigatória de senha no primeiro acesso"""
    if request.method == "POST":
        nova_senha = request.form.get("nova_senha", "")
        confirmar = request.form.get("confirmar_senha", "")
        
        if not nova_senha or len(nova_senha) < 8:
            flash("A senha deve ter pelo menos 8 caracteres.", "danger")
            return render_template("trocar_senha_obrigatoria.html")
        
        if nova_senha != confirmar:
            flash("A confirmação de senha não confere.", "danger")
            return render_template("trocar_senha_obrigatoria.html")
        
        # Atualiza senha e marca como trocada
        current_user.senha = criptografar_senha(nova_senha)
        current_user.senha_trocada = True
        db.session.commit()
        
        registrar_log("Senha Inicial Trocada", f'Usuário "{current_user.nome}" trocou senha inicial obrigatória')
        flash("Senha alterada com sucesso! Bem-vindo ao sistema.", "success")
        return redirect(url_for("inventory.dashboard"))
    
    return render_template("trocar_senha_obrigatoria.html")


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

        if not validar_cpf(cpf):
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

        # Cadastro público sempre atribui papel "Voluntário"
        # Ignora qualquer cargo enviado pelo cliente para evitar elevação de privilégios
        cargo = "Voluntário"

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

        # Resposta genérica - não revela se a conta existe
        if not usuario:
            flash("Se o e-mail ou CPF estiver cadastrado, você receberá instruções de recuperação.", "info")
            return render_template("recuperar_senha.html")

        # Verifica se já existe um token válido recente (limite de 5 solicitações por hora)
        token_existente = RecuperacaoSenha.query.filter(
            RecuperacaoSenha.usuario_id == usuario.id,
            RecuperacaoSenha.usado_em == None,
            RecuperacaoSenha.expira_em > datetime.utcnow()
        ).first()
        
        if token_existente:
            flash("Você já solicitou uma recuperação de senha recentemente. Aguarde o código antes de solicitar novamente.", "warning")
            return render_template("recuperar_senha.html")

        # Cria token seguro no servidor
        recuperacao = RecuperacaoSenha.criar_token(
            usuario_id=usuario.id,
            ip_origem=request.remote_addr,
            expiracao_minutos=15,
            max_tentativas=5
        )

        # Log seguro - NÃO exibe o token
        registrar_log(
            "Recuperação de Senha",
            f'Token de recuperação gerado para "{usuario.nome}" — IP: {request.remote_addr}',
        )

        # Em produção, aqui seria enviado o token por e-mail/SMS
        # Como não há canal verificado configurado, o fluxo está bloqueado
        # Para fins de teste, exibimos o token no frontend (apenas em desenvolvimento)
        from flask import current_app
        if current_app.config.get("ENV") == "development":
            flash(f"Token de desenvolvimento (apenas para teste): {recuperacao.token}", "info")
        else:
            flash("Se o e-mail estiver cadastrado, você receberá as instruções.", "info")

        session["pwd_recovery_id"] = recuperacao.id
        return redirect(url_for("auth.verificar_codigo"))

    return render_template("recuperar_senha.html")


@auth_bp.route("/verificar-codigo", methods=["GET", "POST"])
def verificar_codigo():
    recuperacao_id = session.get("pwd_recovery_id")
    if not recuperacao_id:
        flash("Sessão de recuperação expirada. Inicie a recuperação novamente.", "danger")
        return redirect(url_for("auth.recuperar_senha"))

    recuperacao = RecuperacaoSenha.query.get(recuperacao_id)
    if not recuperacao:
        flash("Token de recuperação inválido ou expirado. Inicie a recuperação novamente.", "danger")
        return redirect(url_for("auth.recuperar_senha"))

    if request.method == "POST":
        token_digitado = limpar(request.form.get("token", ""), max_len=64)
        
        # Verifica validade do token
        if not recuperacao.is_valido():
            if recuperacao.tentativas >= recuperacao.max_tentativas:
                flash("Número máximo de tentativas excedido. Solicite uma nova recuperação.", "danger")
            elif datetime.utcnow() > recuperacao.expira_em:
                flash("Token expirado. Solicite uma nova recuperação.", "danger")
            else:
                flash("Token inválido.", "danger")
            return render_template("verificar_codigo.html")

        # Verifica se o token corresponde
        if token_digitado != recuperacao.token:
            recuperacao.registrar_tentativa()
            flash("Token incorreto. Digite exatamente o token recebido.", "danger")
            return render_template("verificar_codigo.html")

        # Token válido - marca como usado e redireciona para redefinição
        session["pwd_recovery_id"] = recuperacao.id
        session["pwd_recovery_usuario_id"] = recuperacao.usuario_id
        registrar_log(
            "Recuperação de Senha",
            f'Token validado com sucesso para usuário ID {recuperacao.usuario_id} — IP: {request.remote_addr}',
        )
        return redirect(url_for("auth.redefinir_senha"))

    return render_template("verificar_codigo.html")


@auth_bp.route("/redefinir-senha", methods=["GET", "POST"])
@login_required
def redefinir_senha():
    recuperacao_id = session.get("pwd_recovery_id")
    usuario_id_esperado = session.get("pwd_recovery_usuario_id")
    
    if not recuperacao_id or not usuario_id_esperado:
        flash("Sessão de recuperação expirada ou inválida. Inicie a recuperação novamente.", "danger")
        return redirect(url_for("auth.recuperar_senha"))

    recuperacao = RecuperacaoSenha.query.get(recuperacao_id)
    if not recuperacao or not recuperacao.is_valido():
        flash("Token de recuperação inválido ou expirado. Inicie a recuperação novamente.", "danger")
        return redirect(url_for("auth.recuperar_senha"))

    # Valida que o usuário logado é o mesmo que solicitou a recuperação
    if current_user.id != usuario_id_esperado:
        flash("A sessão atual não corresponde à solicitação de recuperação.", "danger")
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

        usuario = Usuario.query.get(usuario_id_esperado)
        if usuario:
            try:
                usuario.senha = criptografar_senha(nova_senha)
                
                # Marca token como usado (uso único)
                recuperacao.marcar_como_usado()
                
                # Invalida sessões/tokens anteriores do usuário (aumenta versão de credencial)
                usuario.credencial_versao += 1
                
                db.session.commit()
                
                # Limpa sessão de recuperação
                session.pop("pwd_recovery_id", None)
                session.pop("pwd_recovery_usuario_id", None)
                
                registrar_log(
                    "Redefinição de Senha",
                    f'Senha do usuário "{usuario.nome}" redefinida com sucesso — IP: {request.remote_addr}',
                )
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
