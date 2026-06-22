import os
from datetime import timedelta

# 1. Define the fallback variables for local development
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "football_league")

# 2. Check if a cloud production database URL exists
RAW_DB_URL = os.environ.get("DATABASE_URL")

if RAW_DB_URL:
    # Render cloud Postgres URLs usually start with 'postgres://'
    # SQLAlchemy 1.4+ strictly requires 'postgresql://' instead
    if RAW_DB_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = RAW_DB_URL.replace("postgres://", "postgresql://", 1)
    else:
        SQLALCHEMY_DATABASE_URI = RAW_DB_URL
else:
    # If no DATABASE_URL env variable exists, default to local MySQL setup
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Rest of your configuration settings below...
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
