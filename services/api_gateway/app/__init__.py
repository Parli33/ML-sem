import logging
from typing import Any

from flask import Flask

from app.config import Config
from app.extensions import csrf, db, login_manager, migrate
from app.infrastructure.models import User
from app.web.auth import auth_blueprint
from app.web.formatters import (
    format_local_datetime,
    format_prediction,
    sort_predictions,
)
from app.web.main import main_blueprint


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config is not None:
        app.config.update(test_config)
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY environment variable is required")
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("DATABASE_URL environment variable is required")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)
    app.add_template_filter(format_prediction, "format_prediction")
    app.add_template_filter(sort_predictions, "sort_predictions")
    app.add_template_filter(
        lambda value: format_local_datetime(value, app.config["APP_TIMEZONE"]),
        "local_datetime",
    )
    app.logger.info(
        "Flask application initialized database=%s ml_api=%s",
        app.config["SQLALCHEMY_DATABASE_URI"].split("@")[-1],
        app.config["ML_API_URL"],
    )

    return app


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    return db.session.get(User, int(user_id))
