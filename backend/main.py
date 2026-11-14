import os
import sys
import logging
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from flask_compress import Compress
from flask_caching import Cache

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.config import Config
from app.database import db, init_db
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
from app.routes.api import api_bp
from app.routes.auth_api import auth_api_bp
from app.routes.qrcode import qrcode_bp
from app.routes.academico import academico_bp
from app.routes.ajuda import ajuda_bp
from app.routes.campanhas import campanhas_bp
from app.routes.impacto import impacto_bp
from app.routes.health import health_bp
from app.routes.admin_health import admin_health_bp
from app.routes.cold_chain_report import cold_chain_report_bp
from app.routes.iot_sync_diagnostic import iot_sync_diagnostic_bp
from app.routes.cold_crisis_lab import cold_crisis_lab_bp
from app.routes.lot_rescue import lot_rescue_bp
from app.routes.iot_integrity_radar import iot_integrity_radar_bp
from app.routes.perfil_resiliencia import perfil_resiliencia_bp
from app.routes.necessidade_institucional import necessidade_institucional_bp
from app.routes.agendamento_entrega import agendamento_entrega_bp
from app.routes.recibo_doacao import recibo_doacao_bp
from app.routes.instituicoes import instituicoes_bp
from app.routes.oferta_medicamento import oferta_medicamento_bp
from app.routes.reserva_oferta import reserva_oferta_bp
from app.routes.matching import matching_bp
from app.routes.aprovacao_farmaceutica import aprovacao_farmaceutica_bp
from app.routes.despacho import despacho_bp
from app.routes.entrega_institucional import entrega_institucional_bp
from app.routes.recibo_entrega import recibo_entrega_bp
from app.routes.receita_anexo import receita_anexo_bp
from app.core.error_handlers import registrar_handlers_api
from app.core.middleware import request_id_middleware

mail = Mail()
csrf = CSRFProtect()
compress = Compress()
cache = Cache()

CSP = {
    "default-src": ["'self'"],
    "script-src": [
        "'self'",
        "'unsafe-inline'",
        "'unsafe-eval'",
        "https://cdn.jsdelivr.net",
        "https://cdnjs.cloudflare.com",
    ],
    "style-src": [
        "'self'",
        "'unsafe-inline'",
        "https://fonts.googleapis.com",
        "https://cdnjs.cloudflare.com",
        "https://unpkg.com",
    ],
    "font-src": [
        "'self'",
        "https://fonts.gstatic.com",
        "https://cdnjs.cloudflare.com",
        "https://unpkg.com",
    ],
    "img-src": [
        "'self'",
        "data:",
        "blob:",
        "https://*.tile.openstreetmap.org",
        "https://*.basemaps.cartocdn.com",
        "https://*.cartocdn.com",
    ],
    "connect-src": [
        "'self'",
        "https://nominatim.openstreetmap.org",
        "https://overpass-api.de",
        "https://*.tile.openstreetmap.org",
        "https://*.basemaps.cartocdn.com",
        "https://viacep.com.br",
    ],
    "worker-src": ["'self'", "blob:"],
    "frame-ancestors": ["'none'"],
    "form-action": ["'self'"],
}


def _inicializar_banco(app, tentativas=6):
    """Cria o esquema e popula a base de referência tolerando corrida entre workers.

    Quando a aplicação sobe com vários workers em paralelo (ex.: gunicorn com
    ``--workers 4``), cada processo executa ``create_all``/seed ao mesmo tempo,
    gerando no MySQL/Postgres erros benignos de corrida ("Table already
    exists" / entrada duplicada) que derrubavam o worker no boot. Como esses
    erros indicam que outro worker já criou/populou a estrutura, faz-se novas
    tentativas até a operação concluir sem erro.
    """
    import time
    from sqlalchemy.exc import SQLAlchemyError
    from app.database import seed_medicamentos_referencia

    for tentativa in range(1, tentativas + 1):
        try:
            db.create_all()
            seed_medicamentos_referencia(app)
            return
        except SQLAlchemyError as exc:
            db.session.rollback()
            mensagem = str(getattr(exc, "orig", exc)).lower()
            benigno = any(marca in mensagem for marca in ("already exists", "1050", "duplicate", "1062", "unique"))
            if benigno and tentativa < tentativas:
                app.logger.warning(
                    "Corrida de inicialização do banco (tentativa %s/%s): %s",
                    tentativa,
                    tentativas,
                    exc,
                )
                time.sleep(0.5 * tentativa)
                continue
            raise


def _executar_seed_demo(app):
    """Popula os dados de apresentação no primeiro arranque (banco vazio).

    A operação é idempotente: só executa quando ainda não há usuários
    cadastrados, de modo que reinícios/redeploys em um banco já populado são
    ignorados. Qualquer falha é registrada no log sem derrubar o boot — a
    aplicação continua no ar mesmo que o seed não conclua.

    O seed roda independentemente de ``DEMO_MODE`` (que controla apenas os
    atalhos visuais de acesso rápido), garantindo que as contas de demonstração
    estejam sempre disponíveis para login, inclusive em produção.
    """
    if app.config.get("TESTING"):
        return

    # O script de seed vive na raiz do projeto (fora de backend/), então garante
    # que a raiz esteja no sys.path para que possa ser importado.
    raiz_projeto = os.path.dirname(BACKEND_DIR)
    if raiz_projeto not in sys.path:
        sys.path.insert(0, raiz_projeto)

    from app.database import db
    from app.models.usuario import Usuario

    try:
        if db.session.query(Usuario.query.exists()).scalar():
            return

        from seed_apresentacao import popular

        app.logger.info("DEMO_MODE ativo e banco vazio: populando dados de apresentação...")
        popular(app)
        app.logger.info("Dados de demonstração carregados com sucesso.")
    except Exception:
        db.session.rollback()
        app.logger.exception(
            "Falha ao popular os dados de demonstração; a aplicação continuará sem os dados de exemplo."
        )


def create_app(config_overrides=None):
    """Create and configure the Flask application.

    ``config_overrides`` is applied before extensions are initialized so test
    suites and other callers can provide an isolated database configuration.
    """
    # Use caminhos absolutos para evitar problemas de diretório de trabalho
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(backend_dir)

    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, "frontend", "templates"),
        static_folder=os.path.join(project_root, "frontend", "static"),
    )
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)
        if app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("sqlite"):
            engine_options = dict(app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}))
            connect_args = dict(engine_options.get("connect_args", {}))
            if "connect_timeout" in connect_args:
                connect_args.pop("connect_timeout")
                connect_args.setdefault("timeout", 5)
                engine_options["connect_args"] = connect_args
                app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options

    logging.basicConfig(level=logging.WARNING)
    app.logger.setLevel(logging.WARNING)

    # ------------------------------------------------------------------
    # Armazenamento local (apresentação/offline)
    # ------------------------------------------------------------------
    # Garante que os diretórios de upload existam já no arranque, para que o
    # envio de receitas/anexos, a geração de QR Codes e os recibos em PDF
    # funcionem 100% em disco local, sem depender de buckets externos.
    for diretorio in (
        app.config.get("PRIVATE_STORAGE_DIR"),
        os.path.join(project_root, "frontend", "static", app.config.get("LOCAL_UPLOAD_DIR", "uploads")),
    ):
        if not diretorio:
            continue
        try:
            os.makedirs(diretorio, exist_ok=True)
        except OSError as exc:
            app.logger.warning("Não foi possível criar o diretório de armazenamento %s: %s", diretorio, exc)

    # Aplicar middleware de request-id e logging estruturado
    request_id_middleware(app)

    mail.init_app(app)
    init_db(app)
    csrf.init_app(app)
    limiter.init_app(app)
    compress.init_app(app)
    cache.init_app(app)
    app.cache = cache

    Talisman(
        app,
        force_https=False,
        strict_transport_security=False,
        content_security_policy=CSP,
        content_security_policy_nonce_in=[],
        referrer_policy="strict-origin-when-cross-origin",
        x_content_type_options=True,
        x_xss_protection=True,
        frame_options="SAMEORIGIN",
        session_cookie_secure=app.config.get("SESSION_COOKIE_SECURE", False),
        session_cookie_http_only=app.config.get("SESSION_COOKIE_HTTPONLY", True),
        session_cookie_samesite=app.config.get("SESSION_COOKIE_SAMESITE", "Lax"),
    )

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor, faça login para acessar o RedeVita."
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        usuario = db.session.get(Usuario, int(user_id))
        # Reject inactive users - invalidate their sessions
        if usuario and not usuario.ativo:
            return None
        return usuario

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
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_api_bp)
    app.register_blueprint(qrcode_bp)
    app.register_blueprint(academico_bp)
    app.register_blueprint(ajuda_bp)
    app.register_blueprint(campanhas_bp)
    app.register_blueprint(impacto_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(admin_health_bp)
    app.register_blueprint(cold_chain_report_bp)
    app.register_blueprint(iot_sync_diagnostic_bp)
    app.register_blueprint(cold_crisis_lab_bp)
    app.register_blueprint(lot_rescue_bp)
    app.register_blueprint(iot_integrity_radar_bp)
    app.register_blueprint(perfil_resiliencia_bp)
    app.register_blueprint(necessidade_institucional_bp)
    app.register_blueprint(agendamento_entrega_bp)
    app.register_blueprint(recibo_doacao_bp)
    app.register_blueprint(instituicoes_bp)
    app.register_blueprint(oferta_medicamento_bp)
    app.register_blueprint(reserva_oferta_bp)
    app.register_blueprint(matching_bp)
    app.register_blueprint(aprovacao_farmaceutica_bp)
    app.register_blueprint(despacho_bp)
    app.register_blueprint(entrega_institucional_bp)
    app.register_blueprint(recibo_entrega_bp)
    app.register_blueprint(receita_anexo_bp)

    registrar_handlers_limite(app)
    registrar_handlers_api(app)

    @app.after_request
    def adicionar_cabecalhos_seguranca(response):
        """Aplica cabeçalhos HTTP de segurança para blindar a aplicação contra ataques comuns."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    @app.route("/")
    def index():
        return render_template("login.html")

    @app.route("/prescriptions")
    def prescriptions_legacy():
        return redirect(url_for("medical.prescriptions"))

    @app.route("/health")
    @app.route("/api/v1/ping")
    def health_check():
        """
        Liveness probe: verifica apenas se o processo Flask está ativo.
        Não depende de dependências externas ou banco de dados.
        Sempre retorna 200 se o servidor está respondendo.
        """
        from flask import jsonify

        return jsonify({"status": "ok", "service": "RedeVita", "type": "liveness"}), 200

    @app.context_processor
    def inject_global_vars():
        """Injeta variáveis globais para todos os templates"""
        from app.models.medicamento import Medicamento

        try:
            alertas = Medicamento.query.filter(Medicamento.status_semaforo == 2).count()
        except Exception:
            alertas = 0

        # Contas de demonstração para o acesso rápido (login) e o seletor de perfil.
        try:
            from app.routes.auth import DEMO_CONTAS, DEMO_ATALHOS, DEMO_SENHA_PADRAO

            demo_mode = bool(app.config.get("DEMO_MODE"))
            demo_contas = DEMO_CONTAS if demo_mode else []
            demo_atalhos = DEMO_ATALHOS if demo_mode else []
            demo_senha = DEMO_SENHA_PADRAO if demo_mode else ""
        except Exception:
            demo_mode = False
            demo_contas = []
            demo_atalhos = []
            demo_senha = ""

        def is_admin():
            """Helper para verificar se usuário é Admin"""
            from flask_login import current_user

            return current_user.is_authenticated and current_user.cargo == "Admin"

        def is_farmaceutico():
            """Helper para verificar se usuário é Farmacêutico"""
            from flask_login import current_user

            return current_user.is_authenticated and current_user.cargo in ["Admin", "Farmacêutico"]

        def is_medico():
            """Helper para verificar se usuário é Médico"""
            from flask_login import current_user

            return current_user.is_authenticated and current_user.cargo in ["Admin", "Médico"]

        def is_operador():
            """Helper para verificar se usuário é Operador"""
            from flask_login import current_user

            return current_user.is_authenticated and current_user.cargo in ["Admin", "Operador"]

        def is_equipe_clinica():
            """Helper para verificar se usuário é da equipe clínica"""
            from flask_login import current_user

            return current_user.is_authenticated and current_user.cargo in [
                "Admin",
                "Operador",
                "Médico",
                "Farmacêutico",
            ]

        def has_cargo(*cargos):
            """Helper para verificar se usuário tem um dos cargos especificados"""
            from flask_login import current_user

            if not current_user.is_authenticated:
                return False
            from app.core.decorators import _cargo_normalizado

            cargo_atual = _cargo_normalizado(current_user.cargo)
            cargos_validos = {_cargo_normalizado(cargo) for cargo in cargos}
            return cargo_atual in cargos_validos

        return {
            "alertas": alertas,
            "is_admin": is_admin,
            "is_farmaceutico": is_farmaceutico,
            "is_medico": is_medico,
            "is_operador": is_operador,
            "is_equipe_clinica": is_equipe_clinica,
            "has_cargo": has_cargo,
            "demo_contas": demo_contas,
            "demo_atalhos": demo_atalhos,
            "demo_senha": demo_senha,
            "demo_mode": demo_mode,
        }

    with app.app_context():
        # Não aplica migrations no startup - use 'flask db upgrade' para isso.
        # A criação do esquema e o seed toleram a corrida entre múltiplos workers.
        _inicializar_banco(app)
        # Em DEMO_MODE, garante que o link online já suba populado (idempotente).
        _executar_seed_demo(app)

    return app


if __name__ == "__main__":
    app = create_app()
    host = os.environ.get("APP_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("APP_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug)
