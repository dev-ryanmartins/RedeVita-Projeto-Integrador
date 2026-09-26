from flask import Blueprint, request, make_response
from flask_login import login_user

from app.core.api_responses import resposta_ok, resposta_erro
from app.core.jwt_auth import gerar_token
from app.core.security import verificar_senha
from app.extensions import limiter
from app.models.usuario import Usuario
from app.utils.log_helper import registrar_log
from app.utils.sanitize import limpar

auth_api_bp = Blueprint("auth_api", __name__, url_prefix="/api/auth")


@auth_api_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login_api():
    dados = request.get_json(silent=True) or {}
    cpf_raw = limpar(str(dados.get("cpf", "")), max_len=20)
    cpf = "".join(filter(str.isdigit, cpf_raw))
    senha = limpar(str(dados.get("senha", "")), max_len=128)

    if not cpf or not senha:
        return resposta_erro("CPF e senha são obrigatórios.", 422)

    usuario = Usuario.query.filter_by(cpf=cpf).first()
    if not usuario or not verificar_senha(usuario.senha, senha):
        registrar_log("Login API Falhou", f"Tentativa inválida (CPF: {cpf[:3]}***)")
        return resposta_erro("CPF ou senha incorretos.", 401)

    if usuario.ativo is False:
        return resposta_erro("Conta desativada.", 403)

    login_user(usuario)
    token = gerar_token(usuario)
    registrar_log("Login API", f'Usuário "{usuario.nome}" autenticado via JWT')

    resposta = make_response(
        resposta_ok(
            {
                "token": token,
                "usuario": {
                    "id": usuario.id,
                    "nome": usuario.nome,
                    "cargo": usuario.cargo,
                    "cpf": usuario.cpf,
                },
            },
            "Login realizado.",
        )
    )
    resposta.set_cookie(
        "redevita_token",
        token,
        httponly=True,
        samesite="Lax",
        max_age=3600,
    )
    return resposta


@auth_api_bp.route("/verificar", methods=["GET"])
def verificar_token():
    from app.core.jwt_auth import autenticar_requisicao

    usuario = autenticar_requisicao()
    if not usuario:
        return resposta_erro("Token inválido ou expirado.", 401)
    return resposta_ok(
        {
            "id": usuario.id,
            "nome": usuario.nome,
            "cargo": usuario.cargo,
        }
    )
