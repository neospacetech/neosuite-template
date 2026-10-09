import os

from flask import Flask

from app.config import CONFIG_BY_NAME
from app.extensions import db, migrate
from app.routes import health_bp


def create_app(config_name: str | None = None) -> Flask:
    env_config = os.getenv("FLASK_ENV")
    selected_config: str = config_name or env_config or "development"
    app = Flask(__name__)
    app.config.from_object(CONFIG_BY_NAME[selected_config])

    if selected_config == "production" and not app.config.get(
        "SQLALCHEMY_DATABASE_URI"
    ):
        raise RuntimeError("DATABASE_URL is required in production")

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(health_bp)

    return app
