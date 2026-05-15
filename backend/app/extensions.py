from flask import jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
    headers_enabled=True,
)


def registrar_handlers_limite(app):
    @app.errorhandler(429)
    def muitas_requisicoes(e):
        from flask import request, render_template
        if request.path.startswith('/api/'):
            return jsonify(erro='Muitas requisições. Aguarde e tente novamente.'), 429
        return render_template('429.html'), 429
