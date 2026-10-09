import os


def _normalize_sqlalchemy_db_url(raw_url: str | None) -> str | None:
    if raw_url is None:
        return None

    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql://", 1)

    if raw_url.startswith("postgresql://"):
        raw_url = raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return raw_url


class BaseConfig:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = _normalize_sqlalchemy_db_url(
        os.getenv(
            "DATABASE_URL", "postgresql+psycopg://postgres:postgres@db:5432/project"
        )
    )


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite+pysqlite:///:memory:"


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = _normalize_sqlalchemy_db_url(os.getenv("DATABASE_URL"))


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
