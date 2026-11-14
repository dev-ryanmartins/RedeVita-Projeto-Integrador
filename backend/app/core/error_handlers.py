from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from flask import request, render_template

from app.core.api_responses import (
    resposta_erro,
    ERRO_VALIDACAO,
    ERRO_NAO_AUTORIZADO,
    ERRO_PROIBIDO,
    ERRO_NAO_ENCONTRADO,
    ERRO_INTERNO,
)
from app.database import db


# Mapeamento de código HTTP -> template HTML amigável (rotas não-API).
_TEMPLATES_ERRO = {
    400: "400.html",
    403: "403.html",
    404: "404.html",
    429: "429.html",
    500: "500.html",
}

# Mapeamento de código HTTP -> código de erro legível por máquina (rotas API).
_CODIGOS_ERRO = {
    400: ERRO_VALIDACAO,
    401: ERRO_NAO_AUTORIZADO,
    403: ERRO_PROIBIDO,
    404: ERRO_NAO_ENCONTRADO,
    429: ERRO_VALIDACAO,
    500: ERRO_INTERNO,
}


def _deseja_json():
    """Detecta se a resposta de erro deve ser JSON (API ou chamada AJAX).

    Rotas sob ``/api/`` são sempre JSON. Para as demais, respeitamos chamadas
    AJAX (``X-Requested-With``) e o cabeçalho ``Accept`` do cliente.
    """
    if request.path.startswith("/api/"):
        return True
    if request.is_json:
        return True
    if request.headers.get("X-Requested-With", "").lower() == "xmlhttprequest":
        return True
    # Só responde JSON se o cliente pedir explicitamente JSON (e não aceitar
    # HTML). Navegadores enviam "text/html,..." e clientes genéricos "*/*" —
    # ambos continuam recebendo a página amigável.
    aceita = request.accept_mimetypes
    return aceita.accept_json and not aceita.accept_html


def _rollback_seguro(app):
    """Faz rollback da sessão engolindo falhas do próprio rollback.

    Garante que a sessão do banco não fique travada após um erro, sem mascarar
    a exceção original caso o rollback também falhe.
    """
    try:
        db.session.rollback()
    except SQLAlchemyError as exc:
        app.logger.warning("Falha ao executar rollback da sessão: %s", exc)
    except Exception as exc:  # pragma: no cover - garantia defensiva
        app.logger.warning("Falha inesperada ao executar rollback: %s", exc)


def _resposta_http(app, e):
    """Constrói a resposta limpa para uma ``HTTPException``."""
    codigo = getattr(e, "code", 500) or 500
    descricao = getattr(e, "description", None) or "Erro na requisição."

    if _deseja_json():
        codigo_erro = _CODIGOS_ERRO.get(codigo, ERRO_INTERNO)
        return resposta_erro(codigo_erro, descricao, codigo)

    template = _TEMPLATES_ERRO.get(codigo)
    if template:
        return render_template(template), codigo
    # Códigos sem template dedicado (ex.: 405, 415) preservam a página padrão.
    return e


def registrar_handlers_api(app):
    @app.errorhandler(400)
    def requisicao_invalida(e):
        return _resposta_http(app, e)

    @app.errorhandler(403)
    def acesso_negado(e):
        return _resposta_http(app, e)

    @app.errorhandler(404)
    def nao_encontrado(e):
        return _resposta_http(app, e)

    @app.errorhandler(500)
    def erro_interno(e):
        _rollback_seguro(app)
        app.logger.error("Erro interno do servidor: %s", e, exc_info=True)
        return _resposta_http(app, e)

    @app.errorhandler(429)
    def muitas_requisicoes(e):
        return _resposta_http(app, e)

    @app.errorhandler(HTTPException)
    def tratar_http(e):
        return _resposta_http(app, e)

    @app.errorhandler(Exception)
    def tratar_excecao_nao_capturada(e):
        # Erros de banco deixam a sessão travada; garante o rollback seguro.
        _rollback_seguro(app)

        if isinstance(e, HTTPException):
            return _resposta_http(app, e)

        app.logger.error("Exceção não tratada capturada: %s", e, exc_info=True)
        if _deseja_json():
            return resposta_erro(ERRO_INTERNO, "Erro interno do servidor.", 500)
        return render_template("500.html"), 500
