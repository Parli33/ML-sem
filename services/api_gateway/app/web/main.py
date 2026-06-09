import logging
from typing import Any, cast

from flask import Blueprint, current_app, flash, render_template
from flask_login import current_user, login_required

from app.infrastructure.ml_api import MlApiError, request_prediction
from app.infrastructure.models import User
from app.services.predictions import get_prediction_history, save_prediction
from app.web.forms import PredictionForm

logger = logging.getLogger(__name__)
main_blueprint = Blueprint("main", __name__)


@main_blueprint.get("/")
@login_required
def index() -> str:
    return render_template("index.html")


@main_blueprint.route("/predict", methods=["GET", "POST"])
@login_required
def predict() -> str:
    form = PredictionForm()
    result: dict[str, Any] | None = None
    if form.validate_on_submit():
        payload = form.to_payload()
        try:
            result = request_prediction(
                current_app.config["ML_API_URL"],
                payload,
                timeout=float(current_app.config["ML_API_TIMEOUT"]),
            )
        except MlApiError as error:
            logger.error("Prediction request failed: %s", error)
            flash(str(error), "danger")
        else:
            user = cast(User, current_user)
            save_prediction(user.id, payload, result)
            flash("Предсказание сохранено в истории.", "success")

    return render_template("predictions/form.html", form=form, result=result)


@main_blueprint.get("/history")
@login_required
def history() -> str:
    user = cast(User, current_user)
    predictions = get_prediction_history(user.id)
    return render_template("predictions/history.html", predictions=predictions)
