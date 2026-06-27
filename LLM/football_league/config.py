import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database connection. Override via env vars or DATABASE_URL. Defaults to SQLite.
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "football_league")

    if os.environ.get("DATABASE_URL"):
        SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    elif DB_USER:
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'football_league.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    # Standings points
    POINTS_WIN = 3
    POINTS_DRAW = 1
    POINTS_LOSS = 0


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    # Tests run against SQLite in-memory so they don't require a live MySQL server.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
