from werkzeug.exceptions import HTTPException

from flask import request, render_template

from app.core.api_responses import resposta_erro
from app.database import db


def registrar_handlers_api(app):
    @app.errorhandler(403)
    def acesso_negado_api(e):
        if request.path.startswith("/api/"):
            return resposta_erro("Acesso negado.", 403)
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def nao_encontrado_api(e):
        if request.path.startswith("/api/"):
            return resposta_erro("Recurso não encontrado.", 404)
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def erro_interno_api(e):
        db.session.rollback()
        app.logger.error("Erro interno do servidor: %s", str(e), exc_info=True)
        if request.path.startswith("/api/"):
            return resposta_erro("Erro interno do servidor.", 500)
        return render_template("500.html"), 500

    @app.errorhandler(HTTPException)
    def tratar_http(e):
        if request.path.startswith("/api/"):
            return resposta_erro(e.description or "Erro na requisição.", e.code)
        if e.code == 404:
            return render_template("404.html"), 404
        if e.code == 403:
            return render_template("403.html"), 403
        if e.code == 500:
            return render_template("500.html"), 500
        return e

    @app.errorhandler(Exception)
    def tratar_excecao_nao_capturada(e):
        db.session.rollback()
        if isinstance(e, HTTPException):
            if request.path.startswith("/api/"):
                return resposta_erro(e.description or "Erro na requisição.", e.code)
            if e.code == 404:
                return render_template("404.html"), 404
            if e.code == 403:
                return render_template("403.html"), 403
            return render_template("500.html"), e.code if hasattr(e, "code") else 500
        app.logger.error("Exceção não tratada capturada: %s", str(e), exc_info=True)
        if request.path.startswith("/api/"):
            return resposta_erro("Erro interno do servidor.", 500)
        return render_template("500.html"), 500

    @app.errorhandler(429)
    def muitas_requisicoes(e):
        if request.path.startswith("/api/"):
            return resposta_erro("Muitas requisições. Aguarde e tente novamente.", 429)
        return render_template("429.html"), 429
