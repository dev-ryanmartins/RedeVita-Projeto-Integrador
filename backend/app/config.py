import os
import hashlib
from dotenv import load_dotenv

load_dotenv()

# Raiz do projeto (…/redevita-projeto-integrador), dois níveis acima de backend/app.
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_INSTANCE_DIR = os.path.join(_PROJECT_ROOT, "instance")
os.makedirs(_INSTANCE_DIR, exist_ok=True)

# Banco SQLite local usado como fallback para apresentação/demonstração.
# Usa caminho ABSOLUTO para que o seed e o servidor apontem sempre para o mesmo
# arquivo, independentemente do diretório de onde a aplicação é iniciada.
SQLITE_FALLBACK_URI = "sqlite:///" + os.path.join(_INSTANCE_DIR, "redevita_demo.db")


def _derivar_segredo_jwt(secret_key: str) -> str:
    """Deriva uma chave JWT determinística e distinta a partir de SECRET_KEY.

    Usada quando ``JWT_SECRET_KEY`` não é definido no ambiente, permitindo que
    uma única ``SECRET_KEY`` configure toda a aplicação sem repetir segredos.
    """
    return hashlib.sha256(("redevita:jwt:" + secret_key).encode("utf-8")).hexdigest()


def _banco_configurado_disponivel(uri: str) -> bool:
    """Verifica rapidamente se um banco externo (MySQL/Postgres) está acessível.

    Usa um timeout curto para não travar o arranque da aplicação quando o
    servidor de banco de dados não estiver ativo no ambiente.
    """
    try:
        from sqlalchemy import create_engine

        connect_args = {}
        if uri.startswith("mysql"):
            connect_args = {"connect_timeout": 3}
        elif uri.startswith("postgresql"):
            connect_args = {"connect_timeout": 3}

        engine = create_engine(
            uri,
            connect_args=connect_args,
            pool_pre_ping=True,
            pool_recycle=280,
        )
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        engine.dispose()
        return True
    except Exception:
        return False


class Config:
    ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    TESTING = os.environ.get("TESTING", "false").lower() == "true"

    # Modo demonstração/apresentação: habilita o "acesso rápido" na tela de login
    # e o seletor de perfil para navegar entre as telas. Ativado por padrão em
    # ambientes que não são de produção e pode ser desligado com DEMO_MODE=false.
    DEMO_MODE = os.environ.get("DEMO_MODE", "true" if ENV != "production" else "false").lower() == "true"

    # ------------------------------------------------------------------
    # Segredos unificados
    # ------------------------------------------------------------------
    # SECRET_KEY é a ÚNICA chave principal obrigatória. SESSION_SECRET e
    # JWT_SECRET_KEY derivam dela automaticamente quando não definidos no
    # ambiente, eliminando a necessidade de configurar três chaves distintas.
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("SESSION_SECRET") or ""

    # Fallback seguro (>= 32 caracteres) para desenvolvimento/apresentação.
    # Garante que a aplicação nunca quebre no arranque por chave ausente/curta,
    # sem depender de um arquivo .env para rodar a demonstração.
    _DEV_SECRET_FALLBACK = "dev-secret-key-change-in-production-32chars-min"

    if ENV == "production":
        # Em produção, falha rápido se a chave principal não existir ou for fraca.
        if len(SECRET_KEY) < 32:
            raise ValueError(
                "SECRET_KEY must be set in production and must be at least 32 characters. "
                "Set a strong, random secret in your environment variables."
            )
    elif len(SECRET_KEY) < 32:
        # Fora de produção, substitui chave ausente/curta por um valor seguro.
        SECRET_KEY = _DEV_SECRET_FALLBACK

    # SESSION_SECRET herda o valor de SECRET_KEY (mesma chave de sessão).
    SESSION_SECRET = os.environ.get("SESSION_SECRET") or SECRET_KEY

    # JWT_SECRET_KEY: usa o valor explícito do ambiente ou deriva um valor
    # determinístico e DISTINTO a partir de SECRET_KEY (>= 32 caracteres),
    # mantendo a separação entre segredo de sessão e de JWT.
    _JWT_SECRET_EXPLICITO = os.environ.get("JWT_SECRET_KEY") or ""
    JWT_SECRET_KEY = _JWT_SECRET_EXPLICITO or _derivar_segredo_jwt(SECRET_KEY)

    if ENV == "production":
        if len(JWT_SECRET_KEY) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters. "
                "Provide a strong value or leave it unset to derive from SECRET_KEY."
            )
        if JWT_SECRET_KEY == SECRET_KEY:
            raise ValueError(
                "JWT_SECRET_KEY must be different from SECRET_KEY. "
                "Leave it unset to derive a distinct value automatically."
            )

    DATABASE_URL = os.environ.get("DATABASE_URL", "")

    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    if DATABASE_URL.startswith("mysql://"):
        DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

    # Em produção, se houver um DATABASE_URL definido, usa-o diretamente — sem
    # fallback silencioso para SQLite, que no Railway é efêmero e perde dados a
    # cada restart. O fallback para SQLite só ocorre quando DATABASE_URL está
    # vazio (ambiente de desenvolvimento/apresentação local).
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = SQLITE_FALLBACK_URI

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    if SQLALCHEMY_DATABASE_URI.startswith("mysql"):
        SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {"connect_timeout": 5}
    elif SQLALCHEMY_DATABASE_URI.startswith("postgresql"):
        SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {"connect_timeout": 5}
    elif SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {"timeout": 5}

    # External integrations
    # ViaCEP public postal-code API (trailing slash kept for safe concatenation)
    VIA_CEP_API_URL = os.environ.get("VIA_CEP_API_URL") or "https://viacep.com.br/ws/"
    # Timeout (segundos) para chamadas à API pública ViaCEP — evita travamento de telas
    VIA_CEP_TIMEOUT = float(os.environ.get("VIA_CEP_TIMEOUT", 5))

    # Email configuration
    # Development/testing default: local SMTP debugging server
    #   python -m smtpd -c DebuggingServer -n localhost 1025
    # Production default: Mailtrap Sandbox (sandbox.smtp.mailtrap.io:2525)
    # Every value can be overridden through environment variables.
    if ENV == "development" or ENV == "testing":
        MAIL_SERVER = os.environ.get("MAIL_SERVER") or "localhost"
        MAIL_PORT = int(os.environ.get("MAIL_PORT") or 1025)
        MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "false").lower() == "true"
        MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() == "true"
        MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
        MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
        MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "RedeVita <noreply@redevita.com>")
        MAIL_DEBUG = os.environ.get("MAIL_DEBUG", "true").lower() == "true"
        # Modo mock/log local: não tenta conectar a nenhum servidor SMTP externo,
        # evitando que telas quebrem por falha de rede no ambiente de apresentação.
        MAIL_SUPPRESS_SEND = os.environ.get("MAIL_SUPPRESS_SEND", "true").lower() == "true"
    else:
        MAIL_SERVER = os.environ.get("MAIL_SERVER") or "sandbox.smtp.mailtrap.io"
        MAIL_PORT = int(os.environ.get("MAIL_PORT") or 2525)
        MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
        MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() == "true"
        MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
        MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
        MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "RedeVita <nao-responda@redevita.com>")
        MAIL_DEBUG = os.environ.get("MAIL_DEBUG", "false").lower() == "true"
        MAIL_SUPPRESS_SEND = os.environ.get("MAIL_SUPPRESS_SEND", "false").lower() == "true"

    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")

    PERMANENT_SESSION_LIFETIME = 3600

    # Session cookie security
    SESSION_COOKIE_SAMESITE = "Lax"

    # In production with HTTPS, cookies must be Secure
    if ENV == "production":
        SESSION_COOKIE_SECURE = True
    else:
        SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"

    SESSION_COOKIE_HTTPONLY = True

    # CSRF protection - enabled by default for security
    # Can be disabled in tests via config_overrides
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    JWT_EXPIRATION = int(os.environ.get("JWT_EXPIRATION", 3600))

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    PROPAGATE_EXCEPTIONS = False

    CACHE_TYPE = os.environ.get("CACHE_TYPE", "SimpleCache")
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", 300))
    CACHE_KEY_PREFIX = "redevita_"

    # QR Code expiration time in minutes (default 15 minutes)
    QR_EXPIRATION_MINUTES = int(os.environ.get("QR_EXPIRATION_MINUTES", 15))

    # ------------------------------------------------------------------
    # Armazenamento local (apresentação/offline)
    # ------------------------------------------------------------------
    # Uploads de receitas/anexos, QR Codes e recibos são gravados em disco
    # local. Nunca dependemos de buckets externos (S3/Cloudinary) no ambiente
    # de demonstração: os diretórios são criados automaticamente no arranque.
    STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local")
    PRIVATE_STORAGE_DIR = os.environ.get("PRIVATE_STORAGE_DIR") or os.path.join(_PROJECT_ROOT, "private", "uploads")
    LOCAL_UPLOAD_DIR = os.environ.get("LOCAL_UPLOAD_DIR", "uploads")
