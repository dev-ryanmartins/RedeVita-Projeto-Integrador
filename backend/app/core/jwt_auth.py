from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, request
from flask_login import current_user, login_user

from app.core.api_responses import resposta_erro
from app.models.usuario import Usuario


def gerar_token(usuario):
    expira = datetime.now(timezone.utc) + timedelta(
        seconds=current_app.config.get("JWT_EXPIRATION", 3600)
    )
    payload = {
        "sub": usuario.id,
        "cpf": usuario.cpf,
        "cargo": usuario.cargo,
        "exp": expira,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm="HS256",
    )


def decodificar_token(token):
    return jwt.decode(
        token,
        current_app.config["JWT_SECRET_KEY"],
        algorithms=["HS256"],
    )


def obter_usuario_do_token(token):
    try:
        payload = decodificar_token(token)
        return Usuario.query.get(int(payload["sub"]))
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, TypeError, ValueError):
        return None


def autenticar_requisicao():
    if current_user.is_authenticated:
        return current_user

    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return obter_usuario_do_token(auth[7:].strip())

    token_cookie = request.cookies.get("redevita_token")
    if token_cookie:
        return obter_usuario_do_token(token_cookie)

    return None


def jwt_ou_sessao_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        usuario = autenticar_requisicao()
        if not usuario or usuario.ativo is False:
            return resposta_erro("Autenticação necessária.", 401)
        if not current_user.is_authenticated:
            login_user(usuario)
        return f(*args, **kwargs)

    return decorated
