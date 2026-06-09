from typing import Any

from app.extensions import db
from app.infrastructure.models import Prediction


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
    db.session.add(prediction)
    db.session.commit()
    return prediction


def get_prediction_history(user_id: int) -> list[Prediction]:
    query = (
        db.select(Prediction)
        .where(Prediction.user_id == user_id)
        .order_by(Prediction.created_at.desc())
    )
    return list(db.session.scalars(query))
