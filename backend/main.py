import os
import logging
from flask import Flask, render_template
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman

from app.config import Config
from app.database import db, init_db, aplicar_migracoes_manuais
from app.extensions import limiter, registrar_handlers_limite
from app.models.usuario import Usuario
from app.routes.auth import auth_bp
from app.routes.inventory import inventory_bp
from app.routes.donation import donation_bp
from app.routes.medicos import medicos_bp
from app.routes.farmacias import farmacias_bp
from app.routes.usuarios import usuarios_bp
from app.routes.relatorios import relatorios_bp
from app.routes.logs import logs_bp
from app.routes.pacientes import pacientes_bp
from app.routes.mapa import mapa_bp
from app.routes.bula import bula_bp
from app.routes.notificacoes import notificacoes_bp
from app.routes.medical import medical_bp
from app.routes.pharmacy import pharmacy_bp
from app.routes.perfil import perfil_bp
from app.routes.busca import busca_bp

mail = Mail()
csrf = CSRFProtect()

CSP = {
    'default-src': ["'self'"],
    'script-src': [
        "'self'",
        "'unsafe-inline'",
        "'unsafe-eval'",
        'https://cdn.jsdelivr.net',
        'https://cdnjs.cloudflare.com',
    ],
    'style-src': [
        "'self'",
        "'unsafe-inline'",
        'https://fonts.googleapis.com',
        'https://cdnjs.cloudflare.com',
    ],
    'font-src': [
        "'self'",
        'https://fonts.gstatic.com',
        'https://cdnjs.cloudflare.com',
    ],
    'img-src': [
        "'self'",
        'data:',
        'blob:',
        'https://*.tile.openstreetmap.org',
        'https://*.basemaps.cartocdn.com',
        'https://*.cartocdn.com',
    ],
    'connect-src': [
        "'self'",
        'https://nominatim.openstreetmap.org',
        'https://overpass-api.de',
        'https://*.tile.openstreetmap.org',
        'https://*.basemaps.cartocdn.com',
        'https://viacep.com.br',
    ],
    'worker-src': ["'self'", "blob:"],
    'frame-ancestors': ["'none'"],
    'form-action': ["'self'"],
}


def create_app():
    app = Flask(
        __name__,
        template_folder='../frontend/templates',
        static_folder='../frontend/static'
    )
    app.config.from_object(Config)

    logging.basicConfig(level=logging.WARNING)
    app.logger.setLevel(logging.WARNING)

    mail.init_app(app)
    init_db(app)
    csrf.init_app(app)
    limiter.init_app(app)

    Talisman(
        app,
        force_https=False,
        strict_transport_security=False,
        content_security_policy=CSP,
        content_security_policy_nonce_in=[],
        referrer_policy='strict-origin-when-cross-origin',
        x_content_type_options=True,
        x_xss_protection=True,
        frame_options='SAMEORIGIN',
        session_cookie_secure=app.config.get('SESSION_COOKIE_SECURE', False),
        session_cookie_http_only=app.config.get('SESSION_COOKIE_HTTPONLY', True),
        session_cookie_samesite=app.config.get('SESSION_COOKIE_SAMESITE', 'Lax'),
    )

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar o RedeVita.'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(donation_bp)
    app.register_blueprint(medicos_bp)
    app.register_blueprint(farmacias_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(relatorios_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(pacientes_bp)
    app.register_blueprint(mapa_bp)
    app.register_blueprint(bula_bp)
    app.register_blueprint(notificacoes_bp)
    app.register_blueprint(medical_bp)
    app.register_blueprint(pharmacy_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(busca_bp)

    registrar_handlers_limite(app)

    @app.route('/')
    def index():
        return render_template('login.html')

    @app.errorhandler(404)
    def pagina_nao_encontrada(e):
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def acesso_negado(e):
        from flask_login import current_user
        from flask import render_template as _render
        return _render('403.html'), 403

    @app.errorhandler(500)
    def erro_interno(e):
        db.session.rollback()
        app.logger.error('Erro interno 500', exc_info=True)
        return render_template('500.html'), 500

    @app.errorhandler(413)
    def payload_muito_grande(e):
        from flask import flash, redirect, url_for
        flash('O dado enviado é muito grande. Verifique os campos e tente novamente.', 'danger')
        return redirect(url_for('auth.login')), 413

    @app.errorhandler(429)
    def muitas_requisicoes(e):
        return render_template('429.html'), 429

    with app.app_context():
        db.create_all()
        aplicar_migracoes_manuais(app)
        _criar_admin_inicial()
        from app.database import seed_medicamentos_referencia
        seed_medicamentos_referencia(app)

    return app


def _criar_admin_inicial():
    from app.core.security import criptografar_senha
    if Usuario.query.first() is None:
        admin = Usuario(
            nome='Administrador',
            cpf='00000000000',
            email='admin@redevita.local',
            senha=criptografar_senha('admin123'),
            cargo='Admin',
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()


if __name__ == '__main__':
    app = create_app()
    host = os.environ.get('APP_HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('APP_DEBUG', 'true').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
