import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class BaseConfig:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-insecure-university-secret-key-2026')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Persistent SQLite storage directory
    DATA_DIR = os.environ.get('DATA_DIR', os.path.join(BASE_DIR, 'data'))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(DATA_DIR, 'course_app.db')}"
    )

    # Session & Cookie Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=4)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

class DevelopmentConfig(BaseConfig):
    """Local development configuration."""
    DEBUG = True

class TestingConfig(BaseConfig):
    """Automated testing configuration with isolated in-memory or temp database."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False  # Disable CSRF in tests for simpler, fast form testing

class ProductionConfig(BaseConfig):
    """Production deployment configuration for Docker / Gunicorn."""
    DEBUG = False
    # If HTTPS is enabled in a reverse proxy, SESSION_COOKIE_SECURE can be set to True
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
