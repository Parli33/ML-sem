import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.infrastructure.models import Prediction

logger = logging.getLogger(__name__)


def save_prediction(
    user_id: int,
    input_data: dict[str, Any],
    result: dict[str, Any],
) -> Prediction:
    prediction = Prediction(
        user_id=user_id,
        input_data=input_data,
        prediction=result,
    )
    try:
        db.session.add(prediction)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Failed to save prediction user_id=%s", user_id)
        raise

    logger.info("Prediction saved id=%s user_id=%s", prediction.id, user_id)
    return prediction


def get_prediction_history(user_id: int) -> list[Prediction]:
    query = (
        db.select(Prediction)
        .where(Prediction.user_id == user_id)
        .order_by(Prediction.created_at.desc())
    )
    try:
        predictions = list(db.session.scalars(query))
    except SQLAlchemyError:
        db.session.rollback()
        logger.exception("Failed to load prediction history user_id=%s", user_id)
        raise

    logger.info(
        "Prediction history loaded user_id=%s count=%s",
        user_id,
        len(predictions),
    )
    return predictions
