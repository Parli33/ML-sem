import logging
from typing import Any, cast

from flask import Blueprint, current_app, flash, render_template
from flask_login import current_user, login_required

from app.infrastructure.ml_api import MlApiError, request_model_info, request_prediction
from app.infrastructure.models import User
from app.services.predictions import get_prediction_history, save_prediction
from app.web.forms import PredictionForm

logger = logging.getLogger(__name__)
main_blueprint = Blueprint("main", __name__)


@main_blueprint.get("/")
@login_required
def index() -> str:
    model_info: dict[str, Any] | None = None
    try:
        model_info = request_model_info(
            current_app.config["ML_API_URL"],
            timeout=float(current_app.config["ML_API_TIMEOUT"]),
        )
    except MlApiError as error:
        logger.warning("Failed to load model info error=%s", error)
    return render_template("index.html", model_info=model_info)


@main_blueprint.route("/predict", methods=["GET", "POST"])
@login_required
def predict() -> str:
    form = PredictionForm()
    result: dict[str, Any] | None = None
    if form.validate_on_submit():
        payload = form.to_payload()
        user = cast(User, current_user)
        logger.info("Prediction requested user_id=%s", user.id)
        try:
            result = request_prediction(
                current_app.config["ML_API_URL"],
                payload,
                timeout=float(current_app.config["ML_API_TIMEOUT"]),
            )
        except MlApiError as error:
            logger.error(
                "Prediction request failed user_id=%s error=%s", user.id, error
            )
            flash(str(error), "danger")
        else:
            prediction = save_prediction(user.id, payload, result)
            logger.info(
                "Prediction completed user_id=%s prediction_id=%s",
                user.id,
                prediction.id,
            )
            flash("Предсказание сохранено в истории.", "success")

    return render_template("predictions/form.html", form=form, result=result)


@main_blueprint.get("/history")
@login_required
def history() -> str:
    user = cast(User, current_user)
    predictions = get_prediction_history(user.id)
    logger.info("History page opened user_id=%s count=%s", user.id, len(predictions))
    return render_template("predictions/history.html", predictions=predictions)
