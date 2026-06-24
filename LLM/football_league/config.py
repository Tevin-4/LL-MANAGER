import os
from datetime import timedelta

# Fallback variables for local development
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "3306")
DB_NAME = os.environ.get("DB_NAME", "football_league")

# Production routing logic
RAW_DB_URL = os.environ.get("DATABASE_URL")

if RAW_DB_URL:
    if RAW_DB_URL.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = RAW_DB_URL.replace("postgres://", "postgresql://", 1)
    else:
        SQLALCHEMY_DATABASE_URI = RAW_DB_URL
else:
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-change-in-production")
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

# Standings points config
POINTS_WIN = 3
POINTS_DRAW = 1
POINTS_LOSS = 0

class Config:
    SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = SQLALCHEMY_TRACK_MODIFICATIONS
    SQLALCHEMY_ENGINE_OPTIONS = SQLALCHEMY_ENGINE_OPTIONS
    JWT_SECRET_KEY = JWT_SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = JWT_ACCESS_TOKEN_EXPIRES
    CORS_ORIGINS = CORS_ORIGINS

config = {
    "development": Config,
    "production": Config,
    "default": Config
}
