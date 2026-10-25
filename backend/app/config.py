import os
import sys
from dotenv import load_dotenv

load_dotenv()


class Config:
    ENV = os.environ.get("FLASK_ENV", "development")
    DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    TESTING = os.environ.get("TESTING", "false").lower() == "true"

    # SECRET_KEY for sessions - must be set in production
    SECRET_KEY = os.environ.get("SESSION_SECRET") or os.environ.get("SECRET_KEY")
    
    # In production, fail fast if secret is not set or is weak
    if ENV == "production":
        if not SECRET_KEY or len(SECRET_KEY) < 32:
            raise ValueError(
                "SESSION_SECRET or SECRET_KEY must be set in production and must be at least 32 characters. "
                "Set a strong, random secret in your environment variables."
            )
    elif not SECRET_KEY:
        # Only allow weak fallback in development/testing
        SECRET_KEY = "dev-secret-key-change-in-production-32chars-min"

    # JWT_SECRET_KEY must be separate from session secret
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    
    if ENV == "production":
        if not JWT_SECRET_KEY or len(JWT_SECRET_KEY) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be set in production and must be at least 32 characters. "
                "Set a strong, random secret different from SESSION_SECRET."
            )
        if JWT_SECRET_KEY == SECRET_KEY:
            raise ValueError(
                "JWT_SECRET_KEY must be different from SESSION_SECRET. "
                "Use separate secrets for session and JWT token signing."
            )
    elif not JWT_SECRET_KEY:
        # In development, generate a different key than session
        JWT_SECRET_KEY = SECRET_KEY + "-jwt-different"

    DATABASE_URL = os.environ.get("DATABASE_URL", "")

    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    if DATABASE_URL.startswith("mysql://"):
        DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL if DATABASE_URL else "sqlite:///redevita.db"
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

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "RedeVita <nao-responda@redevita.com>")

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

    CACHE_REDIS_HOST = os.environ.get("CACHE_REDIS_HOST", "localhost")
    CACHE_REDIS_PORT = int(os.environ.get("CACHE_REDIS_PORT", 6379))
    CACHE_REDIS_DB = int(os.environ.get("CACHE_REDIS_DB", 0))
    CACHE_REDIS_PASSWORD = os.environ.get("CACHE_REDIS_PASSWORD", None)

    # QR Code expiration time in minutes (default 15 minutes)
    QR_EXPIRATION_MINUTES = int(os.environ.get("QR_EXPIRATION_MINUTES", 15))
