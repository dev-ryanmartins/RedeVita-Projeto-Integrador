from werkzeug.exceptions import HTTPException

from flask import request, render_template

from app.core.api_responses import resposta_erro
from app.database import db


def registrar_handlers_api(app):
    @app.errorhandler(HTTPException)
    def tratar_http(e):
        if request.path.startswith("/api/"):
            return resposta_erro(e.description or "Erro na requisição.", e.code)
        return e

    @app.errorhandler(400)
    def bad_request(e):
        if request.path.startswith("/api/"):
            return resposta_erro("Requisição inválida.", 400)
        return render_template("404.html"), 400

    @app.errorhandler(401)
    def nao_autorizado(e):
        if request.path.startswith("/api/"):
            return resposta_erro("Autenticação necessária.", 401)
        from flask import redirect, url_for

        return redirect(url_for("auth.login"))

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

    @app.errorhandler(413)
    def payload_grande(e):
        if request.path.startswith("/api/"):
            return resposta_erro("Payload excede o limite permitido.", 413)
        from flask import flash, redirect, url_for

        flash(
            "O dado enviado é muito grande. Verifique os campos e tente novamente.",
            "danger",
        )
        return redirect(url_for("auth.login")), 413

    @app.errorhandler(500)
    def erro_interno_api(e):
        db.session.rollback()
        app.logger.error("Erro interno", exc_info=True)
        if request.path.startswith("/api/"):
            return resposta_erro("Erro interno do servidor.", 500)
        return render_template("500.html"), 500

    @app.errorhandler(429)
    def muitas_requisicoes(e):
        if request.path.startswith("/api/"):
            return resposta_erro("Muitas requisições. Aguarde e tente novamente.", 429)
        return render_template("429.html"), 429
