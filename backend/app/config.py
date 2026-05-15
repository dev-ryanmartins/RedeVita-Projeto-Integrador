import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'redevita_projeto_ads_2026')

    DATABASE_URL = os.environ.get('DATABASE_URL', '')

    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    if DATABASE_URL.startswith('mysql://'):
        DATABASE_URL = DATABASE_URL.replace('mysql://', 'mysql+pymysql://', 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL if DATABASE_URL else 'sqlite:///redevita.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')

    PERMANENT_SESSION_LIFETIME = 3600

    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True

    WTF_CSRF_ENABLED = False
    WTF_CSRF_TIME_LIMIT = 3600

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    PROPAGATE_EXCEPTIONS = False
